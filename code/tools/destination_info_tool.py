import os
import json
from typing import List, Dict, Any
from tavily import TavilyClient
from langchain.agents import tool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable not set.")

# Load the Tavily API key from your environment variables

def _scrape_and_process_urls(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Scrapes content from a list of URLs using the synchronous Tavily Extract API.
    """
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY environment variable is not set.")

    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    
    results = []
    for url in urls:
        try:
            # The Tavily extract method expects a list of URLs
            response = tavily_client.extract(urls=[url])
            
            # The raw_content is nested within the 'results' list of the response
            content = response["results"][0].get("raw_content") if response and response.get("results") else None
            
            results.append({
                "url": url,
                "content": content
            })
        except Exception as e:
            results.append({
                "url": url,
                "content": None,
                "error": str(e)
            })
    return results

@tool
def get_destination_info(query: str, num_results: int = 5) -> str:
    """
    Performs a web search and extracts content from the most relevant results.

    This function follows Tavily's best practice:
    1. It searches for relevant URLs.
    2. It filters for the most relevant URLs based on a score.
    3. It extracts content only from the top-rated URLs.

    Args:
        query (str): The search query to find information.
        num_results (int): The number of top URLs to extract content from.

    Returns:
        str: A JSON string containing the URL and extracted content for each result.
    """
    if not TAVILY_API_KEY:
        return json.dumps({"error": "Tavily API key not found. Please set the TAVILY_API_KEY environment variable."})

    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        
        # Step 1: Perform the search to get URLs and scores
        search_response = tavily_client.search(
            query=query,
            max_results=3, # Get a larger pool of results to filter from
            search_depth="advanced"
        )
        
        # Step 2: Filter for relevant URLs based on a relevance score
        relevant_urls = [
            result.get('url') for result in search_response.get("results", [])
            if result.get('score', 0) > 0.5
        ]
        
        # Limit to the requested number of results
        urls_to_extract = relevant_urls[:num_results]
        
        if not urls_to_extract:
            return json.dumps({"status": "no_relevant_urls_found"})

        # Step 3: Extract content from the filtered URLs
        extracted_data = _scrape_and_process_urls(urls_to_extract)

        return json.dumps(extracted_data, indent=2)

    except Exception as e:
        return json.dumps({"error": f"An error occurred during search and extraction: {e}"})

if __name__ == "__main__":
    print("---------------------------------------")
    print("Starting Tavily two-step search and extraction...")
    
    # Define the output directory and filename
    output_dir = r"C:\Users\97254\Documents\Ready_Tensor_AI_Course\course_workspace\VacayMate\outputs"
    output_filename = "extracted_data.txt"
    full_path = os.path.join(output_dir, output_filename)
    
    # Get the extracted data as a formatted JSON string
    extracted_data =  get_destination_info.invoke("best things to do in Sofia")
    
    # Check if the output directory exists, if not, create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save the data to the specified file
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(extracted_data)
        
        print("\n---------------------------------------")
        print("Scraping and file saving complete.")
        print(f"Data has been successfully saved to: {full_path}")
        print("---------------------------------------")
        
    except Exception as e:
        print("\n---------------------------------------")
        print("An error occurred while saving the file.")
        print(f"Error: {e}")
        print("---------------------------------------")