import os
import config
from langchain_community.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

class AIController:
    def __init__(self):
        """Initialize the AI controller with a language model"""
        print("Initializing AI controller...")
        
        # Use a small model for testing purposes
        try:
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(config.MODEL_NAME)
            
            # Create text generation pipeline
            local_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                #max_length=100,
                max_new_tokens=50,
                do_sample=True,
                temperature=0.7
            )
            
            # Create LangChain LLM from pipeline
            self.llm = HuggingFacePipeline(pipeline=local_pipeline)
            
            print("AI model loaded successfully")
            
        except Exception as e:
            print(f"Error loading AI model: {e}")
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
            # Use the language model to decide
            decision_chain = LLMChain(llm=self.llm, prompt=self.decision_prompt)
            decision = decision_chain.run(
                page_content=page_content[:1000],  # Truncate to avoid token limits
                current_state=current_state
            )
            return decision.strip()
        else:
            # Simple fallback logic if model isn't available
            if "profile-picture" in page_content:
                return "extract name"
            elif "experience" in page_content:
                return "extract job_title"
            else:
                return "scroll"
    
    def identify_elements(self, page_content, data_type):
        """Identify elements in the page content based on data type"""
        if self.llm:
            # Use the language model to identify elements
            element_chain = LLMChain(llm=self.llm, prompt=self.element_prompt)
            selector = element_chain.run(
                page_content=page_content[:1000],
                data_type=data_type
            )
            return selector.strip()
        else:
            # Simple fallback selectors if model isn't available
            selectors = {
                "name": "h1.text-heading-xlarge",
                "job_title": "div.text-body-medium",
                "company": "span.text-body-small:nth-child(1)",
                "location": "span.text-body-small:nth-child(2)"
            }
            return selectors.get(data_type, "")
    
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
            "profile_picture": "img.profile-picture"
        }
        return selectors.get(data_type, "")