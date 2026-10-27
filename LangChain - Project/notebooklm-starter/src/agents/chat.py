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
    approval_urls: list[str] = None  # URLs requiring approval
    tool_name: str = None  # Name of the tool that triggered interrupt
    tools_used: list[str] = None  # Tools invoked during the execution
    
    def __post_init__(self):
        if self.approval_urls is None:
            self.approval_urls = []
        if self.tools_used is None:
            self.tools_used = []


def _extract_tools_used(result: dict) -> list[str]:
    """Best-effort extraction of tool names from LangGraph messages."""
    tools: list[str] = []
    seen: set[str] = set()

    messages = result.get("messages", []) if isinstance(result, dict) else []

    for message in messages:
        if isinstance(message, dict):
            names = []
            if message.get("name"):
                names.append(str(message["name"]))
            for call in message.get("tool_calls") or []:
                if isinstance(call, dict) and call.get("name"):
                    names.append(str(call["name"]))
            for name in names:
                if name and name not in seen:
                    seen.add(name)
                    tools.append(name)
            continue

        if hasattr(message, "name") and getattr(message, "name"):
            name = str(message.name)
            if name not in seen:
                seen.add(name)
                tools.append(name)

        tool_calls = getattr(message, "tool_calls", None) or []
        if isinstance(tool_calls, list):
            for call in tool_calls:
                name = None
                if isinstance(call, dict):
                    name = call.get("name")
                elif hasattr(call, "name"):
                    name = getattr(call, "name")
                if name and str(name) not in seen:
                    seen.add(str(name))
                    tools.append(str(name))

    return tools



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

Use web_search to find candidate URLs.

Never answer using search snippets.

Search results are candidates only.


4.
HUMAN-IN-THE-LOOP FOR SOURCE SELECTION:

When you find useful webpages from web_search:

DO NOT call scrape_source directly for each URL.

Instead:

Call request_source_approval with the list of discovered URLs.

The HumanInTheLoopMiddleware will interrupt execution
and ask the user to SELECT which sources to add.

IMPORTANT: The user will choose, and the approved URLs will be returned.



5.
After user approval:

You will receive the list of APPROVED URLs.

For each approved URL:

Call sc or crawl_source to save it.

After scraping all approved sources:

Call search_sources again.

Answer ONLY using saved notebook sources.



6.
The approval flow:

request_source_approval(urls: [...])  ← You call this

User sees: "Select which sources to add"

User chooses ✅

You get back: The selected URLs

You then scrape: scrape_source(url) for each selected URL



7.
Never invent information.

If notebook sources do not contain the answer:

Say that more sources are required.



8.
Source priority:

Highest:
1. Approved notebook sources

Lower:
2. Newly approved scraped sources

Never use:
- unapproved webpages
- search snippets
- assumptions



"""



# =====================================================
# Tools
# =====================================================


def make_tools(
        store: SourceStore,
        used_sources:set[str],
        used_tools:set[str],
):


    def track(name:str):
        used_tools.add(name)
        return name


    @tool
    def search_sources(query:str)->str:
        """
        Search notebook vector database.
        """

        track("search_sources")

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

        track("list_sources")

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

        track("get_source")

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
    def request_source_approval(
            urls: list[str]
    ) -> str:
        """
        Ask user to approve and select sources from discovered URLs.
        This tool is protected by HumanInTheLoopMiddleware.
        
        Provides list of URLs and asks user which ones to add to notebook.
        User must explicitly select before sc
        
        Args:
            urls: List of URLs discovered from web search
            
        Returns:
            Confirmation message with approved URLs
        """
        
        print(
            f"🔗 REQUESTING APPROVAL FOR {len(urls)} URLs:"
        )
        
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")
        
        return (
            f"Requesting user approval for {len(urls)} discovered sources. "
            "Please wait for user to select which sources to add."
        )

    
    @tool
    def scrape_source(
            url:str
    )->str:
        """
        Save approved webpage into notebook.
        """
        track("scrape_source")
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

        used_sources.add(source.name)

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

                source = store.add(
                    name=title,
                    content=content
                )

                used_sources.add(source.name)

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
        request_source_approval,
        scrape_source,
        crawl_source,
        deep_web_research

    ]





# =====================================================
# Agent
# =====================================================


checkpointer = InMemorySaver()


def build_agent(used_tools: set[str] | None = None):
    active_tools = used_tools if used_tools is not None else set()
    return create_agent(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=make_tools(
            store,
            set(),
            active_tools,
        ),
        checkpointer=checkpointer,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "request_source_approval": True,
                    "scrape_source": True,
                    "crawl_source": True
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
    used_tools=set()


    config={

        "configurable":{

            "thread_id":thread_id

        }

    }



    agent = build_agent(used_tools)

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

    used_tools = used_tools or set()



    if "__interrupt__" in result:

        # Extract interrupt information
        interrupt_value = result["__interrupt__"][0].value
        interrupt_text = "Please approve the sources to continue."
        
        # Extract tool name and URLs from the interrupt
        tool_name = None
        urls = []
        
        try:
            if hasattr(interrupt_value, 'name'):
                tool_name = interrupt_value.name
            
            if hasattr(interrupt_value, 'args') and isinstance(interrupt_value.args, dict):
                # Handle request_source_approval (multiple URLs)
                if 'urls' in interrupt_value.args:
                    urls = interrupt_value.args.get('urls', [])
                # Handle scrape_source / crawl_source (single URL)
                elif 'url' in interrupt_value.args:
                    urls = [interrupt_value.args['url']]
        except:
            pass

        return Answer(
            text=interrupt_text,
            sources=list(used_sources),
            interrupt=True,
            approval_urls=urls,
            tool_name=tool_name,
            tools_used=sorted(set(_extract_tools_used(result)) | used_tools),
        )


    # Extract the final answer from messages
    final_message = "No response"
    
    if result.get("messages"):
        last_msg = result["messages"][-1]
        content = getattr(last_msg, 'content', None)
        
        if content:
            # Handle list of content blocks (Gemini format)
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                    else:
                        text_parts.append(str(block))
                final_message = ''.join(text_parts)
            else:
                final_message = str(content)

    return Answer(
        text=final_message,
        sources=list(used_sources),
        interrupt=False,
        tools_used=sorted(set(_extract_tools_used(result)) | used_tools),
    )