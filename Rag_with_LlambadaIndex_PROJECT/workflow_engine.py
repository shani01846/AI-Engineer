from __future__ import annotations

import os



# ============================================================
# SSL configuration - must be BEFORE google/gRPC imports
# ============================================================

NETFREE_CA = r"C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt"

os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = NETFREE_CA
os.environ["SSL_CERT_FILE"] = NETFREE_CA
os.environ["REQUESTS_CA_BUNDLE"] = NETFREE_CA

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import gradio as gr
from dotenv import load_dotenv
from netfree_unstrict_ssl import unstrict_ssl
from pinecone import Pinecone
from prepare import (
    ensure_structured_data_file,
    query_structured_data,
    route_query_mode,
)

from llama_index.core import (
    PromptTemplate,
    Settings,
    VectorStoreIndex,
)
from llama_index.core.workflow import (
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.pinecone import PineconeVectorStore


logger = logging.getLogger("workflow_engine")
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)


def configure_ssl_environment() -> None:
    """
    Configure SSL for NetFree + gRPC + Google APIs.
    """

    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = NETFREE_CA
    os.environ["SSL_CERT_FILE"] = NETFREE_CA
    os.environ["REQUESTS_CA_BUNDLE"] = NETFREE_CA

    unstrict_ssl()

    logger.info(
        "SSL CA configured: %s",
        NETFREE_CA
    )


@dataclass
class RuntimeServices:
    index: Optional[VectorStoreIndex]
    prompt: PromptTemplate
    llm_available: bool
    retrieval_available: bool


class RuntimeInitError(RuntimeError):
    pass



def build_runtime_services() -> RuntimeServices:
    """
    Initialize external services lazily.
    """

    load_dotenv()

    cohere_key = os.getenv("COHERE_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    pinecone_key = os.getenv("PINECONE_API_KEY")
    pinecone_index_name = os.getenv(
        "PINECONE_INDEX_NAME",
        "kiro-steering"
    )

    pinecone_namespace = os.getenv(
        "PINECONE_NAMESPACE",
        pinecone_index_name
    )

    allow_offline_fallback = (
        os.getenv(
            "ALLOW_OFFLINE_FALLBACK",
            "1"
        ) == "1"
    )

    disable_gemini = (
        os.getenv(
            "DISABLE_GEMINI",
            "0"
        ) == "1"
    )

    disable_pinecone = (
        os.getenv(
            "DISABLE_PINECONE",
            "0"
        ) == "1"
    )


    missing = [
        name
        for name, value in [
            (
                "COHERE_API_KEY",
                cohere_key
            ),
        ]
        if not value
    ]


    if missing:
        raise RuntimeInitError(
            "חסרים משתני סביבה: "
            + ", ".join(missing)
            + ". יש להגדיר אותם בקובץ .env"
        )


    embed_model = CohereEmbedding(
        api_key=cohere_key,
        model_name="embed-multilingual-v3.0"
    )

    Settings.embed_model = embed_model


    llm_available = False


    if disable_gemini:

        logger.warning(
            "DISABLE_GEMINI=1 - מדלגים על Gemini"
        )


    elif gemini_key:

        try:

            logger.info(
                "Initializing Gemini..."
            )

            Settings.llm = GoogleGenAI(
                model="gemini-flash-latest",
                api_key=gemini_key
            )

            llm_available = True

            logger.info(
                "Gemini initialized successfully."
            )


        except Exception as exc:

            if allow_offline_fallback:

                logger.warning(
                    "Gemini unavailable: %s",
                    exc
                )

                Settings.llm = None

            else:

                raise RuntimeInitError(
                    "Gemini נכשל באתחול."
                ) from exc


    else:

        if not allow_offline_fallback:

            raise RuntimeInitError(
                "GEMINI_API_KEY חסר"
            )


        logger.warning(
            "GEMINI_API_KEY חסר - מצב fallback"
        )

        Settings.llm = None


    retrieval_available = False
    index = None


    if disable_pinecone:

        logger.warning(
            "DISABLE_PINECONE=1"
        )


    elif pinecone_key:

        try:

            pc = Pinecone(
                api_key=pinecone_key
            )

            pinecone_index = pc.Index(
                pinecone_index_name
            )

            vector_store = PineconeVectorStore(
                index=pinecone_index,
                index_name=pinecone_index_name,
                namespace=pinecone_namespace,
            )


            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store
            )

            retrieval_available = True


            logger.info(
                "Pinecone retrieval initialized successfully."
            )


        except Exception as exc:

            if allow_offline_fallback:

                logger.warning(
                    "Pinecone unavailable: %s",
                    exc
                )

            else:

                raise RuntimeInitError(
                    "Pinecone נכשל"
                ) from exc


    else:

        logger.warning(
            "PINECONE_API_KEY חסר - מצב אופליין"
        )


    qa_prompt_tmpl_str = (
        "אתה עוזר טכני מומחה.\n"
        "להלן מידע מתוך הדוקומנטציה:\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "ענה על השאלה:\n"
        "{query_str}"
    )


    return RuntimeServices(
        index=index,
        prompt=PromptTemplate(
            qa_prompt_tmpl_str
        ),
        llm_available=llm_available,
        retrieval_available=retrieval_available,
    )
    # ============================================================
# Workflow Events
# ============================================================

class QueryReceived(Event):
    query: str


class QueryValidated(Event):
    query: str


class SearchAttempt(Event):
    query: str
    top_k: int


class SearchCompleted(Event):
    query: str
    answer: str
    source_count: int
    mode: str


class SearchNeedsRetry(Event):
    query: str
    reason: str


class SearchFailed(Event):
    query: str
    reason: str


class StructuredQueryEvent(Event):
    query: str


class SemanticQueryEvent(Event):
    query: str



class CodingWorkflow(Workflow):

    def __init__(
        self,
        services: RuntimeServices,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.services = services


    @step
    async def ingest(
        self,
        ev: StartEvent
    ) -> QueryReceived:

        query = (
            ev.get("query")
            or ""
        ).strip()

        return QueryReceived(
            query=query
        )


    @step
    async def validate_query(
        self,
        ev: QueryReceived
    ) -> QueryValidated | StopEvent:

        if not ev.query:
            return StopEvent(
                result="השאילתה ריקה"
            )


        if len(ev.query) < 3:
            return StopEvent(
                result="השאלה קצרה מדי"
            )


        return QueryValidated(
            query=ev.query
        )


    @step
    async def route_search(
        self,
        ev: QueryValidated
    ) -> StructuredQueryEvent | SemanticQueryEvent:

        mode = route_query_mode(
            ev.query
        )


        if mode == "structured":

            return StructuredQueryEvent(
                query=ev.query
            )


        return SemanticQueryEvent(
            query=ev.query
        )



    @step
    async def run_structured_search(
        self,
        ev: StructuredQueryEvent
    ) -> SearchCompleted | SearchFailed:

        try:

            ensure_structured_data_file(
                root_dir="kiro-steering",
                output_path="structured_data.json"
            )


            answer = query_structured_data(
                ev.query,
                data_path="structured_data.json"
            )


            return SearchCompleted(
                query=ev.query,
                answer=answer,
                source_count=1,
                mode="structured",
            )


        except Exception as exc:

            return SearchFailed(
                query=ev.query,
                reason=str(exc)
            )



    @step
    async def start_semantic_search(
        self,
        ev: SemanticQueryEvent
    ) -> SearchAttempt:

        return SearchAttempt(
            query=ev.query,
            top_k=3
        )



    @step
    async def run_search(
        self,
        ev: SearchAttempt
    ) -> SearchCompleted | SearchFailed:


        if (
            not self.services.retrieval_available
            or self.services.index is None
        ):

            return SearchCompleted(
                query=ev.query,
                answer=(
                    "המערכת כרגע במצב Offline.\n"
                    "אין גישה ל-Gemini/Pinecone."
                ),
                source_count=0,
                mode="offline",
            )


        try:

            if self.services.llm_available:

                query_engine = (
                    self.services.index
                    .as_query_engine(
                        similarity_top_k=ev.top_k
                    )
                )


                query_engine.update_prompts(
                    {
                        "response_synthesizer:text_qa_template":
                        self.services.prompt
                    }
                )


                response = await query_engine.aquery(
                    ev.query
                )


                answer = str(response)


                source_nodes = (
                    getattr(
                        response,
                        "source_nodes",
                        []
                    )
                    or []
                )


                mode = "llm"



            else:

                retriever = (
                    self.services.index
                    .as_retriever(
                        similarity_top_k=ev.top_k
                    )
                )


                source_nodes = await retriever.aretrieve(
                    ev.query
                )


                answer = "\n".join(
                    [
                        node.node.get_content()[:300]
                        for node in source_nodes
                    ]
                )


                mode = "fallback"



            return SearchCompleted(
                query=ev.query,
                answer=answer,
                source_count=len(source_nodes),
                mode=mode,
            )


        except Exception as exc:

            msg = str(exc)


            if (
                "CERTIFICATE_VERIFY_FAILED"
                in msg
            ):

                return SearchFailed(
                    query=ev.query,
                    reason="בעיית SSL מול שירות חיצוני"
                )


            return SearchFailed(
                query=ev.query,
                reason=msg
            )



    @step
    async def handle_failure(
        self,
        ev: SearchFailed
    ) -> StopEvent:

        return StopEvent(
            result=
            f"המערכת נכשלה: {ev.reason}"
        )



    @step
    async def format_result(
        self,
        ev: SearchCompleted
    ) -> StopEvent:


        return StopEvent(
            result=(
                ev.answer
                + "\n\n---\n"
                + f"מצב: {ev.mode}\n"
                + f"מקורות: {ev.source_count}"
            )
        )



_SERVICES: Optional[RuntimeServices] = None
_INIT_ERROR: Optional[str] = None



def get_services():

    global _SERVICES, _INIT_ERROR


    if _SERVICES:
        return _SERVICES


    try:

        _SERVICES = build_runtime_services()

        logger.info(
            "Runtime initialized"
        )

        return _SERVICES


    except Exception as exc:

        _INIT_ERROR = str(exc)

        logger.exception(
            "Runtime initialization failed"
        )

        return None



async def run_workflow_async(
    query: str
):

    services = get_services()


    if services is None:

        return (
            "אתחול נכשל: "
            + str(_INIT_ERROR)
        )


    workflow = CodingWorkflow(
        services=services
    )


    handler = workflow.run(
        query=query
    )

    result = await handler


    return str(result)


def run_workflow(
    query: str
):

    # Gradio may already run inside an event loop; keep the UI callback sync
    # and run async workflow logic in an isolated loop.
    return asyncio.run(
        run_workflow_async(
            query
        )
    )



def launch_ui():

    demo = gr.Interface(
        fn=run_workflow,
        inputs=gr.Textbox(
            label="שאלה לדוקומנטציה"
        ),
        outputs=gr.Textbox(
            label="תשובה"
        ),
        title="ChipUp RAG Assistant",
    )


    demo.launch()



if __name__ == "__main__":

    configure_ssl_environment()

    print(
        "GRPC SSL:",
        os.environ.get(
            "GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"
        )
    )

    print(
        "SSL CERT:",
        os.environ.get(
            "SSL_CERT_FILE"
        )
    )


    launch_ui()
# from __future__ import annotations
# import os

# os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = (
#     r"C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt"
# )
# import asyncio
# import logging
# import os
# from dataclasses import dataclass
# from typing import Optional

# import certifi
# import gradio as gr
# from dotenv import load_dotenv
# from netfree_unstrict_ssl import unstrict_ssl
# from pinecone import Pinecone
# from prepare import ensure_structured_data_file, query_structured_data, route_query_mode

# from llama_index.core import PromptTemplate, Settings, VectorStoreIndex
# from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step
# from llama_index.embeddings.cohere import CohereEmbedding
# from llama_index.llms.gemini import Gemini
# from llama_index.vector_stores.pinecone import PineconeVectorStore


# logger = logging.getLogger("workflow_engine")
# logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# def configure_ssl_environment() -> None:
#     """Configure SSL hints while keeping sane defaults for libraries that support certifi."""
#     unstrict_ssl()
#     os.environ.setdefault("SSL_CERT_FILE", certifi.where())
#     os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())


# @dataclass
# class RuntimeServices:
#     index: Optional[VectorStoreIndex]
#     prompt: PromptTemplate
#     llm_available: bool
#     retrieval_available: bool


# class RuntimeInitError(RuntimeError):
#     pass


# def build_runtime_services() -> RuntimeServices:
#     """Initialize external services lazily so startup doesn't crash on network/SSL issues."""
#     load_dotenv()

#     cohere_key = os.getenv("COHERE_API_KEY")
#     gemini_key = os.getenv("GEMINI_API_KEY")
#     pinecone_key = os.getenv("PINECONE_API_KEY")
#     pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "kiro-steering")
#     pinecone_namespace = os.getenv("PINECONE_NAMESPACE", pinecone_index_name)
#     allow_offline_fallback = os.getenv("ALLOW_OFFLINE_FALLBACK", "1") == "1"
#     disable_gemini = os.getenv("DISABLE_GEMINI", "0") == "1"
#     disable_pinecone = os.getenv("DISABLE_PINECONE", "0") == "1"

#     missing = [
#         name
#         for name, value in [
#             ("COHERE_API_KEY", cohere_key),
#         ]
#         if not value
#     ]

#     if missing:
#         raise RuntimeInitError(
#             "חסרים משתני סביבה: " + ", ".join(missing) + ". יש להגדיר אותם בקובץ .env"
#         )

#     embed_model = CohereEmbedding(api_key=cohere_key, model_name="embed-multilingual-v3.0")
#     Settings.embed_model = embed_model

#     llm_available = False
#     if disable_gemini:
#         logger.warning("DISABLE_GEMINI=1 - מדלגים על אתחול Gemini.")
#     elif gemini_key:
#         try:
#             # Gemini initialization may perform network calls; keep graceful fallback when SSL blocks it.
#             Settings.llm = Gemini(model="gemini-1.5-flash", api_key=gemini_key)
#             llm_available = True
#             logger.info("Gemini initialized successfully.")
#         except Exception as exc:  # noqa: BLE001
#             if allow_offline_fallback:
#                 logger.warning("Gemini unavailable (fallback mode): %s", str(exc))
#                 # Explicitly disable any default LLM to prevent OpenAI fallback
#                 Settings.llm = None
#             else:
#                 raise RuntimeInitError(
#                     "Gemini נכשל באתחול ו-ALLOW_OFFLINE_FALLBACK=0. בדקי SSL/GEMINI_API_KEY."
#                 ) from exc
#     else:
#         if not allow_offline_fallback:
#             raise RuntimeInitError(
#                 "GEMINI_API_KEY חסר ו-ALLOW_OFFLINE_FALLBACK=0."
#             )
#         logger.warning("GEMINI_API_KEY חסר - המערכת תרוץ במצב fallback ללא LLM.")
#         # Explicitly disable any default LLM to prevent OpenAI fallback
#         Settings.llm = None

#     retrieval_available = False
#     index: Optional[VectorStoreIndex] = None
#     if disable_pinecone:
#         logger.warning("DISABLE_PINECONE=1 - מדלגים על אתחול Pinecone.")
#     elif pinecone_key:
#         try:
#             pc = Pinecone(api_key=pinecone_key)
#             pinecone_index = pc.Index(pinecone_index_name)
#             vector_store = PineconeVectorStore(
#                 index=pinecone_index,
#                 index_name=pinecone_index_name,
#                 namespace=pinecone_namespace,
#             )
#             index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
#             retrieval_available = True
#             logger.info("Pinecone retrieval initialized successfully.")
#         except Exception as exc:  # noqa: BLE001
#             if allow_offline_fallback:
#                 logger.warning("Pinecone unavailable (offline fallback): %s", str(exc))
#             else:
#                 raise RuntimeInitError(
#                     "Pinecone נכשל באתחול ו-ALLOW_OFFLINE_FALLBACK=0. בדקי SSL/PINECONE_API_KEY."
#                 ) from exc
#     else:
#         if not allow_offline_fallback:
#             raise RuntimeInitError(
#                 "PINECONE_API_KEY חסר ו-ALLOW_OFFLINE_FALLBACK=0."
#             )
#         logger.warning("PINECONE_API_KEY חסר - המערכת תרוץ במצב אופליין ללא Retrieval.")

#     qa_prompt_tmpl_str = (
#         "אתה עוזר טכני מומחה. להלן מידע מתוך הדוקומנטציה של הפרויקט:\n"
#         "---------------------\n"
#         "{context_str}\n"
#         "---------------------\n"
#         "בהתבסס על המידע לעיל בלבד, ענה על השאלה הבאה: {query_str}\n"
#         "אם אין מספיק מידע בקונטקסט, ציין זאת במפורש ובקש הבהרה."
#     )

#     return RuntimeServices(
#         index=index,
#         prompt=PromptTemplate(qa_prompt_tmpl_str),
#         llm_available=llm_available,
#         retrieval_available=retrieval_available,
#     )


# # --- Workflow Events ---
# class QueryReceived(Event):
#     query: str


# class QueryValidated(Event):
#     query: str


# class SearchAttempt(Event):
#     query: str
#     top_k: int


# class SearchCompleted(Event):
#     query: str
#     answer: str
#     source_count: int
#     mode: str


# class SearchNeedsRetry(Event):
#     query: str
#     reason: str


# class SearchFailed(Event):
#     query: str
#     reason: str


# class StructuredQueryEvent(Event):
#     query: str


# class SemanticQueryEvent(Event):
#     query: str


# class CodingWorkflow(Workflow):
#     def __init__(self, services: RuntimeServices, **kwargs):
#         super().__init__(**kwargs)
#         self.services = services

#     @step
#     async def ingest(self, ev: StartEvent) -> QueryReceived:
#         query = (ev.get("query") or "").strip()
#         return QueryReceived(query=query)

#     @step
#     async def validate_query(self, ev: QueryReceived) -> QueryValidated | StopEvent:
#         if not ev.query:
#             return StopEvent(result="השאילתה ריקה. כתבי שאלה קצרה וברורה.")

#         if len(ev.query) < 3:
#             return StopEvent(result="השאילתה קצרה מדי (פחות מ-3 תווים).")

#         # Basic nonsense/noise guard
#         cleaned = ev.query.replace(" ", "")
#         if len(set(cleaned)) == 1:
#             return StopEvent(result="נראה שהקלט לא תקין (תו חוזר). נסי לנסח שאלה אמיתית.")

#         return QueryValidated(query=ev.query)

#     @step
#     async def route_search(self, ev: QueryValidated) -> StructuredQueryEvent | SemanticQueryEvent:
#         mode = route_query_mode(ev.query)
#         if mode == "structured":
#             return StructuredQueryEvent(query=ev.query)
#         return SemanticQueryEvent(query=ev.query)

#     @step
#     async def run_structured_search(self, ev: StructuredQueryEvent) -> SearchCompleted | SearchFailed:
#         try:
#             ensure_structured_data_file(root_dir="kiro-steering", output_path="structured_data.json")
#             answer = query_structured_data(ev.query, data_path="structured_data.json")
#             return SearchCompleted(
#                 query=ev.query,
#                 answer=answer,
#                 source_count=1,
#                 mode="structured",
#             )
#         except Exception as exc:  # noqa: BLE001
#             return SearchFailed(query=ev.query, reason=f"Structured query failed: {exc}")

#     @step
#     async def start_semantic_search(self, ev: SemanticQueryEvent) -> SearchAttempt:
#         return SearchAttempt(query=ev.query, top_k=3)

#     @step
#     async def run_search(self, ev: SearchAttempt) -> SearchCompleted | SearchNeedsRetry | SearchFailed:
#         if not self.services.retrieval_available or self.services.index is None:
#             offline_answer = (
#                 "המערכת פועלת במצב אופליין בגלל חסימת SSL לרשת חיצונית. "
#                 "גרדיו תקין וה-Workflow רץ, אך אין כרגע גישה ל-Pinecone/Gemini.\n\n"
#                 "מה אפשר לעשות עכשיו:\n"
#                 "1. לפתוח גישת SSL ל-api.pinecone.io ולשירותי Google Gemini.\n"
#                 "2. או להריץ ברשת אחרת / VPN שבו תעודות SSL תקינות.\n"
#                 "3. להשאיר ALLOW_OFFLINE_FALLBACK=1 כדי להמשיך בדיקות ממשק."
#             )
#             return SearchCompleted(
#                 query=ev.query,
#                 answer=offline_answer,
#                 source_count=0,
#                 mode="offline",
#             )

#         try:
#             if self.services.llm_available:
#                 query_engine = self.services.index.as_query_engine(similarity_top_k=ev.top_k)
#                 query_engine.update_prompts(
#                     {"response_synthesizer:text_qa_template": self.services.prompt}
#                 )
#                 response = query_engine.query(ev.query)
#                 answer = str(response).strip()
#                 source_nodes = getattr(response, "source_nodes", None) or []
#                 mode = "llm"
#             else:
#                 # Fallback retrieval mode: retrieve documents directly without LLM synthesis
#                 # This avoids any dependency on OpenAI or other LLM services.
#                 retriever = self.services.index.as_retriever(similarity_top_k=ev.top_k)
#                 source_nodes = retriever.retrieve(ev.query)
                
#                 if not source_nodes:
#                     answer = ""
#                 else:
#                     preview_lines = []
#                     for idx, node in enumerate(source_nodes[:3], start=1):
#                         text = (node.node.get_content() if hasattr(node, 'node') else node.get_content()).strip().replace("\n", " ")
#                         preview = (text[:220] + "...") if len(text) > 220 else text
#                         preview_lines.append(f"{idx}. {preview}")
                    
#                     answer = (
#                         "Gemini לא זמין כרגע (כנראה SSL/רשת), לכן מוצג סיכום מבוסס אחזור בלבד:\n\n"
#                         + "\n".join(preview_lines)
#                     )
#                 mode = "fallback"
#         except Exception as exc:  # noqa: BLE001
#             msg = str(exc)
#             if "CERTIFICATE_VERIFY_FAILED" in msg or "Ssl handshake failed" in msg:
#                 return SearchFailed(
#                     query=ev.query,
#                     reason="שגיאת SSL מול ספק חיצוני. בדקי תעודות/חומת אש/NetFree.",
#                 )
#             return SearchFailed(query=ev.query, reason=f"שגיאת חיפוש: {msg}")

#         source_count = len(source_nodes)

#         if not answer or answer.lower() in {"none", "null"}:
#             return SearchNeedsRetry(query=ev.query, reason="לא התקבלה תשובה.")

#         if source_count == 0:
#             return SearchNeedsRetry(query=ev.query, reason="לא נמצאו מקורות תומכים.")

#         return SearchCompleted(
#             query=ev.query,
#             answer=answer,
#             source_count=source_count,
#             mode=mode,
#         )

#     @step
#     async def handle_retry(self, ev: SearchNeedsRetry) -> SearchAttempt | StopEvent:
#         expanded_query = f"{ev.query} הסבר טכני מפורט"
#         if len(expanded_query) > 280:
#             return StopEvent(result=f"לא נמצאו תוצאות מספקות: {ev.reason}")
#         return SearchAttempt(query=expanded_query, top_k=5)

#     @step
#     async def handle_failure(self, ev: SearchFailed) -> StopEvent:
#         return StopEvent(result=f"המערכת נתקלה בתקלה: {ev.reason}")

#     @step
#     async def format_result(self, ev: SearchCompleted) -> StopEvent:
#         confidence = "גבוה" if ev.source_count >= 3 else "בינוני"
#         mode_label = "LLM מלא" if ev.mode == "llm" else "Fallback אחזור"
#         if ev.mode == "offline":
#             mode_label = "Offline דמו"
#             confidence = "נמוך"
#         if ev.mode == "structured":
#             mode_label = "Structured Data"
#             confidence = "גבוה"
#         output = (
#             f"{ev.answer}\n\n"
#             f"---\n"
#             f"מצב הרצה: {mode_label}\n"
#             f"מדדי איכות: מקורות שנמצאו={ev.source_count}, confidence={confidence}"
#         )
#         return StopEvent(result=output)


# _SERVICES: Optional[RuntimeServices] = None
# _INIT_ERROR: Optional[str] = None


# def get_services() -> Optional[RuntimeServices]:
#     global _SERVICES, _INIT_ERROR
#     if _SERVICES is not None:
#         return _SERVICES

#     try:
#         _SERVICES = build_runtime_services()
#         logger.info("Runtime services initialized successfully.")
#         return _SERVICES
#     except Exception as exc:  # noqa: BLE001
#         _INIT_ERROR = str(exc)
#         logger.exception("Runtime initialization failed")
#         return None


# async def run_workflow(query: str) -> str:
#     services = get_services()
#     if services is None:
#         return f"אתחול המערכת נכשל: {_INIT_ERROR}"

#     workflow = CodingWorkflow(services=services)
#     result = await workflow.run(query=query)
#     return str(result)


# def launch_ui() -> None:
#     demo = gr.Interface(
#         fn=run_workflow,
#         inputs=gr.Textbox(label="שאלה לדוקומנטציה"),
#         outputs=gr.Textbox(label="תשובה מהמערכת"),
#         title="ChipUp RAG Assistant",
#         description="שאלי שאלה על הדוקומנטציה ותקבלי תשובה מבוססת הקשר.",
#     )
#     demo.launch()


# if __name__ == "__main__":
#     configure_ssl_environment()
#     launch_ui()
