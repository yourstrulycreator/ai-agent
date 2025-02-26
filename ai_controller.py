import os
import config
from langchain_community.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import time
import random

class AIController:
    def __init__(self):
        """Initialize the AI controller with a language model"""
        print("Initializing AI controller...")
        
        # Set device based on availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Retry mechanism for model loading
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
            You are an AI agent browsing LinkedIn, specifically focusing on alumni and school pages. 
            Given the current page content and state, decide what action to take next.
            
            Current page content: {page_content}
            Current state: {current_state}
            
            Context about LinkedIn pages:
            1. School alumni pages show lists of people associated with the institution
            2. Profile cards typically contain name, title, current employer, and sometimes location
            3. These cards often have a consistent structure but may vary in exact class names
            4. Profile cards are usually wrapped in a container with class names like "artdeco-entity-lockup"
            
            Possible actions:
            1. scroll (to load more profiles)
            2. click [selector] (to navigate to a profile or section)
            3. extract [data_type] (to get information from the current view)
            4. wait (to allow page elements to load)
            5. visit_profile [url] (to visit a person's profile page)
            6. back (to navigate back to previous page)
            
            Your decision (just return the action):
            """
        )
        
        # Enhanced prompt template for element identification for LinkedIn
        self.element_prompt = PromptTemplate(
            input_variables=["page_content", "data_type"],
            template="""
            Analyze this LinkedIn page content and identify the CSS selector
            that would target the {data_type} element.
            
            Page content: {page_content}
            
            LinkedIn commonly uses these patterns:
            - Names: .artdeco-entity-lockup__title, .org-people-profile-card__profile-title
            - Titles: .artdeco-entity-lockup__subtitle, .org-people-profile-card__profile-subtitle
            - Companies: .artdeco-entity-lockup__caption, .org-people-profile-card__profile-info
            - Profile Cards: .artdeco-entity-lockup, .org-people-profile-card, .search-result__info
            
            CSS selector for {data_type}:
            """
        )
        
        # New prompt template for profile page analysis
        self.profile_page_prompt = PromptTemplate(
            input_variables=["page_content"],
            template="""
            Analyze this LinkedIn profile page content to extract the following information:
            1. Current employer/company name
            2. Job title
            3. Location
             4. Years of experience (if available)
            
            Page content: {page_content}
            
            Return only the extracted information in this format:
            employer: [company name]
            job_title: [job title]
            location: [location]
            experience_years: [years]
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
        page_lower = page_content.lower()
        if "profile-picture" in page_lower:
            return "extract name"
        elif "experience" in page_lower:
            return "extract job_title"
        elif "education" in page_lower:
            return "extract education"
        elif "skills" in page_lower:
            return "extract skills"
        else:
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
    
    def analyze_profile_containers(self, page_html):
        """Analyze the page HTML to identify the structure of profile containers"""
        if self.llm:
            try:
                profile_analysis_prompt = PromptTemplate(
                    input_variables=["page_html"],
                    template="""
                    Analyze this LinkedIn page HTML and identify the structure of PEOPLE profile cards.
                    
                    HTML fragment: {page_html}
                    
                    IMPORTANT: Focus ONLY on containers that represent individual PEOPLE profiles.
                    Ignore organizational pages, company profiles, or "People also viewed" sections.
                    
                    Look specifically for elements containing:
                    - Person's name (first and last)
                    - Person's title/occupation
                    - Person's current employer
                    
                    Return your analysis in this format:
                    container_selector: [your selector]
                    name_selector: [your selector]
                    title_selector: [your selector]
                    company_selector: [your selector]
                    """
                )
                
                analysis_chain = LLMChain(llm=self.llm, prompt=profile_analysis_prompt)
                analysis = analysis_chain.run(page_html=page_html[:3000])  # Limit to avoid token issues
                
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
