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
        
        # Create prompt templates for decision making
        self.decision_prompt = PromptTemplate(
            input_variables=["page_content", "current_state"],
            template="""
            You are an AI agent browsing LinkedIn. Given the current page content and state,
            decide what action to take next.
            
            Current page content: {page_content}
            Current state: {current_state}
            
            Possible actions:
            1. scroll
            2. click [selector]
            3. extract [data_type]
            4. wait
            
            Your decision (just return the action):
            """
        )
        
        # Create prompt template for element identification
        self.element_prompt = PromptTemplate(
            input_variables=["page_content", "data_type"],
            template="""
            Analyze this LinkedIn page content and identify the CSS selector
            that would target the {data_type} element.
            
            Page content: {page_content}
            
            CSS selector for {data_type}:
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
    
    def fallback_selectors(self, data_type):
        """Provide fallback selectors for LinkedIn elements"""
        # These selectors may need to be updated based on LinkedIn's current layout
        selectors = {
            "name": "h1.text-heading-xlarge",
            "job_title": "div.text-body-medium",
            "company": "span.text-body-small:nth-child(1)",
            "location": "span.text-body-small:nth-child(2)",
            "about": "section.summary div.display-flex p",
            "experience": "section.experience h3",
            "education": "section.education h3",
            "profile_picture": "img.profile-picture",
            "skills": "section[id*='skills'] span.display-text",
            "recommendations": "section[id*='recommendations'] span.inline-show-more-text"
        }
        return selectors.get(data_type, "")