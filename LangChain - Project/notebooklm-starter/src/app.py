from netfree_unstrict_ssl import unstrict_ssl
unstrict_ssl()

from dotenv import load_dotenv
load_dotenv()

from agents import chat
from core.store import store
import io
import sys

# Fix encoding for Hebrew and emoji support
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main() -> None:
    print('📓 NotebookLM - Testing Chat Agent')
    print('=' * 50)
    
    # Test 1: Add a test source
    print('\nTest 1: Adding a source')
    test_content = """
    LangChain is a framework for developing applications powered by language models.
    It enables applications that are:
    - Data-aware: Connect a language model to other sources of data
    - Agentic: Allow a language model to interact with its environment
    
    The framework is built with Python and provides tools for RAG, agents, and more.
    """
    source = store.add("test_source.txt", test_content)
    print(f"Added source: {source.id} - {source.name}")
    print(f"Active sources: {[s.name for s in store.list()]}")
    
    # Test 2: Search the sources directly
    print('\nTest 2: Direct vector search')
    docs = store.search("What is LangChain?", k=5)
    print(f"Found {len(docs)} documents")
    for doc in docs:
        print(f"   - {doc.metadata.get('source', 'unknown')}")
    
    # Test 3: Query via agent (without web search)
    print('\nTest 3: Querying through agent')
    result = chat.answer("What is LangChain? Keep it brief.", "test-thread-2")
    print(f"Response: {result.text[:150]}...")
    print(f"Sources used: {result.sources}")
    print(f"Interrupted: {result.interrupt}")
    
    print('\n' + '=' * 50)
    print('All tests completed successfully!')

if __name__ == "__main__":
    main()