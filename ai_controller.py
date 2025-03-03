import os
import config
from langchain_huggingface import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import time
import random
from langchain_openai import ChatOpenAI
import requests

# Remove these deprecated imports
# from langchain.llms import OpenAI
# from langchain.chat_models import ChatOpenAI
# from langchain_community.llms import HuggingFacePipeline
from langchain.chat_models import ChatOpenAI
import requests

class AIController:
    def __init__(self):
        """Initialize the AI controller with a language model"""
        print("Initializing AI controller...")
        
        # Set device based on availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Check for OpenRouter API key - first in config, then in environment
        self.api_key = getattr(config, "OPENROUTER_API_KEY", None) or os.environ.get("OPENROUTER_API_KEY")
        
        if self.api_key:
            # Try to initialize OpenRouter first
            print("OpenRouter API key found, attempting to initialize...")
            self.llm = self._initialize_openrouter()
            if self.llm:
                print("Using OpenRouter for AI capabilities")
                return  # Skip local model initialization
            else:
                print("OpenRouter initialization failed, falling back to local model")
        else:
            print("No OpenRouter API key found, using local model")
        
        # Retry mechanism for model loading (only if OpenRouter not available)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Load tokenizer and model
                tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
                model = AutoModelForCausalLM.from_pretrained(
                    config.MODEL_NAME, 
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                ).to(self.device)
                
                # Create text generation pipeline
                local_pipeline = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=100,
                    do_sample=True,
                    temperature=0.7,
                    device=self.device
                )
                
                # Create LangChain LLM from pipeline
                self.llm = HuggingFacePipeline(pipeline=local_pipeline)
                
                print("AI model loaded successfully")
                break
                
            except Exception as e:
                print(f"Error loading AI model (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Wait before retrying
                    time.sleep(random.uniform(1, 3))
                else:
                    # Fallback to a simplified AI controller
                    self.llm = None
                    print("Using simplified AI controller instead")
        
        # Enhanced prompt templates for decision making with LinkedIn context
        self.decision_prompt = PromptTemplate(
            input_variables=["page_content", "current_state"],
            template="""
            TASK: Decide the next action to take while browsing LinkedIn.
            
            CONTEXT:
            - You are an AI agent browsing LinkedIn, focusing on alumni and school pages
            - School alumni pages show lists of people associated with the institution
            - Profile cards typically contain name, title, current employer, and sometimes location
            - These cards often have a consistent structure but may vary in exact class names
            - Profile cards are usually wrapped in a container with class names like "artdeco-entity-lockup"
            
            CURRENT STATE:
            - Page content: {page_content}
            - Current state: {current_state}
            
            POSSIBLE ACTIONS:
            1. scroll (to load more profiles)
            2. click [selector] (to navigate to a profile or section)
            3. extract [data_type] (to get information from the current view)
            4. wait (to allow page elements to load)
            5. visit_profile [url] (to visit a person's profile page)
            6. back (to navigate back to previous page)
            
            INSTRUCTIONS:
            - Analyze the current page content and state
            - Choose the most appropriate next action
            - Return ONLY the action without explanation
            """
        )
        
        # Enhanced prompt template for element identification for LinkedIn
        self.element_prompt = PromptTemplate(
            input_variables=["page_content", "data_type"],
            template="""
            TASK: Identify the CSS selector for a specific element type on a LinkedIn page.
            
            CONTEXT:
            LinkedIn commonly uses these patterns:
            - Names: .artdeco-entity-lockup__title, .org-people-profile-card__profile-title
            - Titles: .artdeco-entity-lockup__subtitle, .org-people-profile-card__profile-subtitle
            - Companies: .artdeco-entity-lockup__caption, .org-people-profile-card__profile-info
            - Profile Cards: .artdeco-entity-lockup, .org-people-profile-card, .search-result__info
            
            INPUT:
            - Element type to find: {data_type}
            - Page HTML content: {page_content}
            
            INSTRUCTIONS:
            - Analyze the HTML content
            - Find the most specific and reliable CSS selector for the {data_type} element
            - Return ONLY the CSS selector without explanation
            """
        )
        
        # New prompt template for profile page analysis
        self.profile_page_prompt = PromptTemplate(
            input_variables=["page_content"],
            template="""
            TASK: Extract professional information from a LinkedIn profile page.
            
            INPUT:
            LinkedIn profile HTML: {page_content}
            
            INSTRUCTIONS:
            1. Analyze the HTML content of the LinkedIn profile
            2. Extract the following information:
               - Current employer/company name
               - Job title
               - Location
               - Years of experience (if available)
            
            OUTPUT FORMAT:
            employer: [company name]
            job_title: [job title]
            location: [location]
            experience_years: [years]
            
            Return ONLY the extracted information in the exact format above.
            """
        )
        
    def decide_next_action(self, page_content, current_state):
        """Decide the next action based on the current page content and state"""
        if self.llm:
            try:
                # Truncate and clean the page content to avoid token limits
                truncated_content = page_content[:1500]  # Increased from 1000
                
                # Use the language model to decide
                decision_chain = LLMChain(llm=self.llm, prompt=self.decision_prompt)
                decision = decision_chain.run(
                    page_content=truncated_content,
                    current_state=current_state
                )
                return decision.strip()
            except Exception as e:
                print(f"Error in AI decision making: {e}")
                # Fallback to simple logic
                return self._fallback_decision(page_content)
        else:
            # Simple fallback logic if model isn't available
            return self._fallback_decision(page_content)
    
    def _fallback_decision(self, page_content):
        """Simple rule-based fallback decision logic"""
        # This is a minimal fallback that only triggers if the AI model fails completely
        # It will simply scroll to continue exploration rather than attempting extraction
        return "scroll"
    
    def identify_elements(self, page_content, data_type):
        """Identify elements in the page content based on data type"""
        if self.llm:
            try:
                # Use the language model to identify elements
                element_chain = LLMChain(llm=self.llm, prompt=self.element_prompt)
                selector = element_chain.run(
                    page_content=page_content[:1500],
                    data_type=data_type
                )
                result = selector.strip()
                
                # Verify the selector is reasonable
                if len(result) > 200 or not any(c in result for c in ['.', '#', '[']):
                    print(f"Invalid selector returned by AI: {result}")
                    return self.fallback_selectors(data_type)
                    
                return result
            except Exception as e:
                print(f"Error in AI element identification: {e}")
                return self.fallback_selectors(data_type)
        else:
            # Simple fallback selectors if model isn't available
            return self.fallback_selectors(data_type)
    
    def preprocess_html(self, html_content):
        """Pre-process HTML to reduce token count while preserving structure"""
        import re
        
        # Remove non-essential elements that consume tokens
        html_content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html_content)
        html_content = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html_content)
        html_content = re.sub(r'<!--(.*?)-->', '', html_content)
        
        # Remove long attribute values that don't affect structure
        html_content = re.sub(r'(data-[^=]+=)["\'][^"\']{50,}["\']', r'\1"..."', html_content)
        html_content = re.sub(r'(aria-[^=]+=)["\'][^"\']{20,}["\']', r'\1"..."', html_content)
        
        # Keep class names but remove other lengthy attributes
        html_content = re.sub(r'((?!class=)[a-z-]+=)["\'][^"\']{30,}["\']', r'\1"..."', html_content)
        
        return html_content

    def analyze_profile_containers(self, page_html):
        """Analyze the page HTML to identify the structure of profile containers"""
        if self.llm:
            try:
                # Pre-process HTML to reduce token count while preserving structure
                processed_html = self.preprocess_html(page_html)
                
                # Update the profile container analysis prompt
                profile_analysis_prompt = PromptTemplate(
                    input_variables=["page_html"],
                    template="""
                    TASK: Identify the structure of people profile cards on a LinkedIn page.
                    
                    INPUT:
                    HTML fragment: {page_html}
                    
                    INSTRUCTIONS:
                    1. Focus ONLY on containers that represent individual PEOPLE profiles
                    2. Ignore organizational pages, company profiles, or "People also viewed" sections
                    3. Look specifically for elements containing:
                       - Person's name (first and last)
                       - Person's title/occupation
                       - Person's current employer
                    
                    OUTPUT FORMAT:
                    container_selector: [CSS selector for the profile container]
                    name_selector: [CSS selector for the name element]
                    title_selector: [CSS selector for the title element]
                    company_selector: [CSS selector for the company element]
                    
                    Return ONLY the selectors in the exact format above.
                    """
                )
                
                analysis_chain = LLMChain(llm=self.llm, prompt=profile_analysis_prompt)
                analysis = analysis_chain.run(page_html=processed_html[:2500])  # Adjusted limit
                
                # Parse the results
                result = {}
                for line in analysis.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        result[key.strip()] = value.strip()
                
                return result
            except Exception as e:
                print(f"Error in AI container analysis: {e}")
                return {}
        else:
            # Improved fallback selectors specifically for LinkedIn people cards
            return {
                "container_selector": ".search-result__wrapper",
                "name_selector": ".actor-name",
                "title_selector": ".search-result__info .subline-level-1",
                "company_selector": ".search-result__info .subline-level-2"
            }
    
    def _initialize_openrouter(self):
        """Initialize OpenRouter as the LLM provider"""
        try:
            # Import OpenAI client
            from openai import OpenAI
            from langchain.llms.base import LLM
            from typing import Any, List, Mapping, Optional
            
            # Create a custom LLM class that uses OpenRouter directly
            class OpenRouterLLM(LLM):
                client: Any = None  # Initialize with default value
                model: str = ""     # Initialize with default value
                
                def __init__(self, api_key, model="qwen/qwen-2.5-coder-32b-instruct:free"):
                    super().__init__()
                    self.client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=api_key,
                    )
                    self.model = model
                
                def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
                    try:
                        completion = self.client.chat.completions.create(
                            extra_headers={
                                "HTTP-Referer": "https://linkedin-agent.local",
                                "X-Title": "LinkedIn Data Extraction Agent",
                            },
                            model=self.model,
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            temperature=0.2,
                            max_tokens=4096,
                        )
                        return completion.choices[0].message.content
                    except Exception as e:
                        print(f"Error in OpenRouter API call: {e}")
                        return "Error processing request"
                
                @property
                def _llm_type(self) -> str:
                    return "openrouter"
                
                @property
                def _identifying_params(self) -> Mapping[str, Any]:
                    return {"model": self.model}
            
            # Create and return the custom LLM
            llm = OpenRouterLLM(api_key=self.api_key)
            
            # Test the LLM with a simple prompt to verify it works
            test_result = llm._call("Hello, are you working?")
            print(f"OpenRouter test response received: {len(test_result)} characters")
            
            return llm
            
        except Exception as e:
            print(f"Error initializing OpenRouter: {e}")
            return None
    
    def _initialize_local_model(self):
        """Initialize local model as fallback"""
        # Your existing local model initialization code
        pass

    def analyze_profile_page(self, page_content):
        """Extract detailed profile information from a LinkedIn profile page using AI"""
        if self.llm:
            try:
                # Preprocess the content to reduce token count
                processed_content = self.preprocess_html(page_content)
                
                # Enhanced prompt template with more specific instructions
                enhanced_profile_prompt = PromptTemplate(
                    input_variables=["page_content"],
                    template="""
                    TASK: Extract the EXACT current job information from this LinkedIn profile HTML.
    
                    HTML: {page_content}
                    
                    IMPORTANT INSTRUCTIONS:
                    1. Look for the CURRENT position (usually marked with "Present" in date range)
                    2. Extract the EXACT text as it appears on the profile
                    3. DO NOT generate or guess information - only extract what's actually in the HTML
                    4. Look for sections with class names containing "experience", "position", or "title"
                    5. Pay special attention to the first/top position listed in the experience section
                    6. If you can't find the information, return "Not found" instead of making up data
                    
                    Return ONLY:
                    employer: [company name exactly as it appears]
                    job_title: [job title exactly as it appears]
                    
                    DO NOT invent generic titles like "Software Engineer" if they don't appear in the profile.
                    """
                )
                
                # Use the language model to analyze the profile page
                profile_chain = LLMChain(llm=self.llm, prompt=enhanced_profile_prompt)
                analysis = profile_chain.run(page_content=processed_content[:8000])
                
                # Parse the results
                result = {}
                for line in analysis.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()  # Normalize keys
                        value = value.strip()
                        # Accept valid values, avoid placeholder text
                        if value and not (('[' in value and ']' in value) or value == 'N/A' or value == 'None' or value == 'Not found'):
                            result[key] = value
                
                print(f"AI extraction results: {result}")
                return result
            except Exception as e:
                print(f"Error in AI profile analysis: {e}")
                return {}
        else:
            # Return empty dict if model isn't available
            return {}

    # Fix indentation - this should be a top-level method, not nested
    def analyze_profile_with_hints(self, page_content, job_title_hint, employer_hint):
        """
        Extract profile information using human-provided hints.
        
        Args:
            page_content: The HTML content of the profile page
            job_title_hint: Text that appears near or in the job title
            employer_hint: Text that appears near or in the employer name
            
        Returns:
            dict: The extracted profile information
        """
        if not self.llm:
            print("No LLM available for profile analysis")
            return {}
        
        try:
            # Preprocess the content to reduce token count but ensure we keep enough
            processed_content = self.preprocess_html(page_content)
            
            # Check if we're truncating too much content
            original_length = len(page_content)
            processed_length = len(processed_content)
            print(f"Original HTML length: {original_length} characters")
            print(f"Processed HTML length: {processed_length} characters")
            print(f"Reduction: {(1 - processed_length/original_length)*100:.1f}%")
            
            # Create a guided prompt with the human hints
            guided_prompt = PromptTemplate(
                input_variables=["page_content", "job_title_hint", "employer_hint"],
                template="""
                TASK: Extract the exact current job information from this LinkedIn profile HTML.
                
                HTML: {page_content}
                
                HUMAN GUIDANCE:
                - The job title contains or is near text like: "{job_title_hint}"
                - The employer contains or is near text like: "{employer_hint}"
                
                INSTRUCTIONS:
                1. Use the human guidance to locate the relevant sections in the HTML
                2. Extract the EXACT text as it appears on the profile
                3. Look for elements containing the hint text or nearby elements
                4. Pay special attention to the experience section
                5. If you find multiple matches, prioritize the current position (with "Present" in date)
                
                Return ONLY:
                employer: [company name exactly as it appears]
                job_title: [job title exactly as it appears]
                """
            )
            
            # Use the language model to analyze with the guided prompt
            guided_chain = LLMChain(llm=self.llm, prompt=guided_prompt)
            analysis = guided_chain.run(
                page_content=processed_content,
                job_title_hint=job_title_hint,
                employer_hint=employer_hint
            )
            
            # Parse the results
            result = {}
            for line in analysis.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()  # Normalize keys
                    value = value.strip()
                    # Accept valid values, avoid placeholder text
                    if value and not (('[' in value and ']' in value) or value == 'N/A' or value == 'None' or value == 'Not found'):
                        result[key] = value
            
            print(f"AI extraction results with hints: {result}")
            return result
            
        except Exception as e:
            print(f"Error in AI profile analysis with hints: {e}")
            return {}
    
    def analyze_single_profile(self, page_content, save_to_file=True):
        """
        Analyze a single LinkedIn profile in detail and save the results to help train the AI.
        
        Args:
            page_content: The HTML content of the profile page
            save_to_file: Whether to save the analysis to a file
            
        Returns:
            dict: The extracted profile information
        """
        if not self.llm:
            print("No LLM available for profile analysis")
            return {}
        
        try:
            # Preprocess the content to reduce token count but keep more content for training
            processed_content = self.preprocess_html(page_content)
            
            # Create a more detailed prompt for single profile analysis
            detailed_profile_prompt = PromptTemplate(
                input_variables=["page_content"],
                template="""
                TASK: Perform a detailed analysis of this LinkedIn profile HTML to extract job information.
                
                INPUT:
                HTML content: {page_content}
                
                INSTRUCTIONS:
                1. First identify the main sections of the profile (Experience, Education, etc.)
                2. For the Experience section:
                   - List ALL job positions found, from most recent to oldest
                   - For each position, extract: title, company name, and date range
                   - Indicate which position appears to be current/most recent
                3. Look for structural patterns that indicate job information:
                   - How job titles are formatted and where they appear
                   - How company names are formatted and where they appear
                   - How date ranges are formatted
                4. Explain your reasoning for identifying the current position
                
                OUTPUT FORMAT:
                sections_found: [list of main sections identified]
                current_position:
                  job_title: [title]
                  employer: [company]
                  date_range: [dates]
                all_positions:
                  - position1:
                      job_title: [title]
                      employer: [company]
                      date_range: [dates]
                  - position2:
                      job_title: [title]
                      employer: [company]
                      date_range: [dates]
                structural_patterns:
                  job_title_pattern: [description of pattern]
                  employer_pattern: [description of pattern]
                  date_pattern: [description of pattern]
                reasoning: [explanation of how you identified the current position]
                
                Return the information in the exact format above.
                """
            )
            
            # Use the language model to analyze the profile page
            profile_chain = LLMChain(llm=self.llm, prompt=detailed_profile_prompt)
            analysis = profile_chain.run(page_content=processed_content[:12000])  # Use larger context for training
            
            print("\n--- DETAILED PROFILE ANALYSIS ---")
            print(analysis)
            print("--------------------------------\n")
            
            # Save the analysis to a file if requested
            if save_to_file:
                import json
                from datetime import datetime
                
                # Extract basic results for standard format
                result = {}
                for line in analysis.strip().split('\n'):
                    if line.startswith('current_position:'):
                        continue
                    if ':' in line and not line.strip().endswith(':'):
                        key, value = line.split(':', 1)
                        key = key.strip()
                        if key in ['job_title', 'employer'] and not (value.strip().startswith('[') and value.strip().endswith(']')):
                            result[key] = value.strip()
                
                # Create data directory if it doesn't exist
                os.makedirs("/Users/lu/Dev/ai-agent/data", exist_ok=True)
                
                # Save the full analysis for training purposes
                timestamp = datetime.now().isoformat()
                with open(f"/Users/lu/Dev/ai-agent/data/profile_analysis_{timestamp}.txt", "w") as f:
                    f.write(analysis)
                
                # Also save a simplified version with just the extracted data
                with open(f"/Users/lu/Dev/ai-agent/data/profile_data_{timestamp}.json", "w") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"Saved profile analysis to data/profile_analysis_{timestamp}.txt")
                print(f"Saved simplified data to data/profile_data_{timestamp}.json")
                
                return result
            
            # Parse basic results if not saving to file
            result = {}
            for line in analysis.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key in ['job_title', 'employer'] and not (value.startswith('[') and value.endswith(']')):
                        result[key] = value
            
            return result
            
        except Exception as e:
            print(f"Error in detailed profile analysis: {e}")
            return {}
        else:
            # Return empty dict if model isn't available
            return {}
    
    def fallback_selectors(self, data_type):
        """Provide fallback selectors for LinkedIn elements"""
        # These selectors may need to be updated based on LinkedIn's current layout
        selectors = {
            "name": "h1.text-heading-xlarge",
            "job_title": "div.text-body-medium",
            "company": "span.text-body-small:nth-child(1)",
            "location": "span.text-body-small:nth-child(2)",  # Fixed syntax error here
            "about": "section.summary div.display-flex p",
            "experience": "section.experience h3",
            "education": "section.education h3",
            "profile_picture": "img.profile-picture",
            "skills": "section[id*='skills'] span.display-text",
            "recommendations": "section[id*='recommendations'] span.inline-show-more-text"
        }
        return selectors.get(data_type, "")
