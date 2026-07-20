from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from core.store import SourceStore, store
from core.sources import format_docs
from core.firecrawl import (
    search_web,
    scrape_web,
    crawl_web,
)


# =====================================================
# Response
# =====================================================

@dataclass
class Answer:
    text: str
    sources: list[str]
    interrupt: bool = False



# =====================================================
# Model
# =====================================================

MODEL = ChatGoogleGenerativeAI(
    model="gemini-flash-lite-latest",
    temperature=0,
)



# =====================================================
# Prompt
# =====================================================

SYSTEM_PROMPT = """

You are an assistant for a NotebookLM style application.

Your job is to answer questions using ONLY approved notebook sources.


Available tools:

search_sources:
Search existing saved notebook documents.

web_search:
Find candidate webpages.
Search results are NOT sources.

scrape_source:
Save a webpage into the notebook.
This tool is protected by HumanInTheLoopMiddleware.
The middleware will automatically ask the user for approval before execution.

crawl_source:
Save multiple webpages into the notebook.
This tool is protected by HumanInTheLoopMiddleware.

deep_web_research:
Find multiple candidate URLs.
This tool only discovers URLs and does not save anything.



RULES:


1.
Always start with search_sources.


2.
If the answer exists in notebook sources:

Answer only using those sources.


3.
If information is missing:

Use web_search.

Never answer using search snippets.

Search results are candidates only.


4.
IMPORTANT HUMAN-IN-THE-LOOP FLOW:

When you find useful webpages:

DO NOT ask the user for approval in normal text.

DO NOT write:
"Would you like me to scrape these pages?"

Instead:

Call scrape_source or crawl_source.

The HumanInTheLoopMiddleware will automatically interrupt execution
and request approval from the user.

Never bypass this mechanism.



5.
After the user approves:

Continue execution.

The approved tool must:

- scrape the webpage
- save it into the notebook
- add it to the vector store

Then:

- call search_sources again
- answer only from saved notebook sources



6.
For deep research:

Use deep_web_research when multiple sources are needed.

It only collects URLs.

After collecting URLs:

Use scrape_source or crawl_source for selected URLs.

The middleware handles approval.



7.
Never invent information.

If approved notebook sources do not contain the answer:

Say that more sources are required.



8.
Source priority:

Highest priority:
1. Approved notebook sources

Lower priority:
2. Newly approved scraped sources

Never use:
- search snippets
- unapproved webpages
- assumptions



"""



# =====================================================
# Tools
# =====================================================


def make_tools(
        store: SourceStore,
        used_sources:set[str]
):


    @tool
    def search_sources(query:str)->str:
        """
        Search notebook vector database.
        """

        print(
            "🔎 VECTOR SEARCH:",
            query
        )


        docs = store.search(query)


        if not docs:
            return "No sources found."


        used_sources.update(
            d.metadata.get(
                "source",
                "unknown"
            )
            for d in docs
        )


        return format_docs(docs)



    @tool
    def list_sources()->str:
        """
        List available notebook sources.
        """

        return "\n".join(
            f"{s.id}: {s.name}"
            for s in store.list()
        )



    @tool
    def get_source(
            source_id:str
    )->str:
        """
        Get full source content.
        """

        source = store.get(source_id)

        if not source:
            return "Source not found."


        return source.content



    @tool
    def web_search(
            query:str
    )->str:
        """
        Search web.
        Returns candidates only.
        """

        print(
            "🌐 WEB SEARCH:",
            query
        )


        results = search_web(query)


        output=[]


        for r in results[:5]:


            title = getattr(
                r,
                "title",
                ""
            )

            url = getattr(
                r,
                "url",
                ""
            )


            description = getattr(
                r,
                "description",
                ""
            )


            output.append(
f"""
TITLE:
{title}

URL:
{url}

DESCRIPTION:
{description}
"""
            )


        return "\n".join(output)




    @tool
    def scrape_source(
            url:str
    )->str:
        """
        Save approved webpage into notebook.
        """

        print(
            "📥 SCRAPING:",
            url
        )


        content = scrape_web(url)


        if isinstance(content,dict):

            content = content.get(
                "markdown",
                ""
            )


        if not content:

            return "Scraping failed."


        source = store.add(
            name=url,
            content=content
        )


        print(
            "✅ SAVED:",
            source.name
        )


        return (
            "Source saved successfully:\n"
            + source.name
        )




    @tool
    def crawl_source(
            url:str
    )->str:
        """
        Crawl approved website.
        """

        pages = crawl_web(url)


        count=0


        for page in pages:


            if hasattr(page,"markdown"):

                content = page.markdown

                title = getattr(
                    page,
                    "title",
                    url
                )


            else:

                content = page.get(
                    "markdown",
                    ""
                )


                title = page.get(
                    "metadata",
                    {}
                ).get(
                    "title",
                    url
                )


            if content:

                store.add(
                    name=title,
                    content=content
                )

                count+=1



        return f"Added {count} sources."




    @tool
    def deep_web_research(
            topic:str
    )->str:
        """
        Find multiple URLs.
        Does not save.
        """

        queries=[

            topic,
            f"What is {topic}",
            f"{topic} overview",
            f"{topic} guide",
            f"{topic} tutorial",
            f"{topic} documentation",
            f"{topic} best practices",
            f"{topic} examples",
            f"{topic} latest",
            f"{topic} analysis"

        ]


        urls=[]


        for q in queries:


            results = search_web(q)


            for r in results[:3]:

                url=getattr(
                    r,
                    "url",
                    None
                )

                if url:

                    urls.append(url)



        urls=list(set(urls))


        return (
            "Found URLs requiring approval:\n\n"
            +
            "\n".join(urls[:10])
        )



    return [

        search_sources,
        list_sources,
        get_source,
        web_search,
        scrape_source,
        crawl_source,
        deep_web_research

    ]





# =====================================================
# Agent
# =====================================================


checkpointer = InMemorySaver()



def build_agent():


    return create_agent(

        model=MODEL,

        system_prompt=SYSTEM_PROMPT,

        tools=make_tools(
            store,
            set()
        ),


        checkpointer=checkpointer,


        middleware=[

            HumanInTheLoopMiddleware(

                interrupt_on={

                    "scrape_source":True,

                    "crawl_source":True

                }

            )

        ]

    )



agent = build_agent()





# =====================================================
# Run
# =====================================================


def answer(
        question:str,
        thread_id:str
):


    used_sources=set()


    config={

        "configurable":{

            "thread_id":thread_id

        }

    }



    result = agent.invoke(

        {
            "messages":[
                {
                    "role":"user",
                    "content":question
                }
            ]
        },

        config=config

    )



    if "__interrupt__" in result:


        return Answer(

            text=str(
                result["__interrupt__"][0].value
            ),

            sources=[],

            interrupt=True

        )



    interrupt = result["__interrupt__"][0].value


    return Answer(
        text="Waiting for approval",
        sources=[],
        interrupt=True,
    )