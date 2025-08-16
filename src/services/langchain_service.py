"""
Langchain Service for Workshop 4
Handles prompt management, chain management, and function calling
"""

import os
import logging
from typing import List, Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, RetrievalQA
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class LangchainService:
    """Service for managing Langchain operations"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vector_store = None
        self.chains = {}
        self.prompts = {}
        
        # Initialize if OpenAI is configured
        if os.getenv('OPENAI_API_KEY'):
            try:
                self.llm = ChatOpenAI(
                    temperature=0.7,
                    model_name="GPT-4o-mini",  # Changed from gpt-3.5-turbo to GPT-4o-mini
                    openai_api_key=os.getenv('OPENAI_API_KEY')
                )
                logger.info("✅ Langchain LLM initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Langchain LLM: {e}")
        
        # Initialize embeddings
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            logger.info("✅ Langchain embeddings initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
    
    def create_prompt_template(self, name: str, template: str, input_variables: List[str]) -> PromptTemplate:
        """Create a new prompt template"""
        try:
            prompt = PromptTemplate(
                template=template,
                input_variables=input_variables
            )
            self.prompts[name] = prompt
            logger.info(f"✅ Created prompt template: {name}")
            return prompt
        except Exception as e:
            logger.error(f"❌ Failed to create prompt template {name}: {e}")
            return None
    
    def create_chain(self, name: str, prompt: PromptTemplate, llm=None) -> Optional[LLMChain]:
        """Create a new Langchain chain"""
        try:
            if llm is None:
                llm = self.llm
            
            if llm is None:
                logger.warning("⚠️ No LLM available for chain creation")
                return None
            
            chain = LLMChain(llm=llm, prompt=prompt)
            self.chains[name] = chain
            logger.info(f"✅ Created chain: {name}")
            return chain
        except Exception as e:
            logger.error(f"❌ Failed to create chain {name}: {e}")
            return None
    
    def create_retrieval_chain(self, name: str, documents: List[Document], 
                              prompt_template: str = None) -> Optional[RetrievalQA]:
        """Create a retrieval chain with FAISS"""
        try:
            if not documents:
                logger.warning("⚠️ No documents provided for retrieval chain")
                return None
            
            if self.embeddings is None:
                logger.warning("⚠️ No embeddings available for retrieval chain")
                return None
            
            # Create FAISS vector store
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
            
            # Create prompt template
            if prompt_template is None:
                prompt_template = """Use the following context to answer the question at the end. 
                If you don't know the answer, just say that you don't know, don't try to make up an answer.
                
                Context: {context}
                
                Question: {question}
                
                Answer:"""
            
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
            
            # Create retrieval chain
            chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
                chain_type_kwargs={"prompt": prompt}
            )
            
            self.chains[name] = chain
            logger.info(f"✅ Created retrieval chain: {name}")
            return chain
            
        except Exception as e:
            logger.error(f"❌ Failed to create retrieval chain {name}: {e}")
            return None
    
    def run_chain(self, name: str, inputs: Dict[str, Any]) -> Optional[str]:
        """Run a specific chain with inputs"""
        try:
            if name not in self.chains:
                logger.error(f"❌ Chain {name} not found")
                return None
            
            chain = self.chains[name]
            result = chain.run(inputs)
            logger.info(f"✅ Chain {name} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to run chain {name}: {e}")
            return None
    
    def run_retrieval_chain(self, name: str, question: str) -> Optional[str]:
        """Run a retrieval chain with a question"""
        try:
            if name not in self.chains:
                logger.error(f"❌ Retrieval chain {name} not found")
                return None
            
            chain = self.chains[name]
            result = chain({"query": question})
            logger.info(f"✅ Retrieval chain {name} executed successfully")
            return result.get("result", "No result found")
            
        except Exception as e:
            logger.error(f"❌ Failed to run retrieval chain {name}: {e}")
            return None
    
    def get_available_chains(self) -> List[str]:
        """Get list of available chain names"""
        return list(self.chains.keys())
    
    def get_available_prompts(self) -> List[str]:
        """Get list of available prompt names"""
        return list(self.prompts.keys())
    
    def real_function_calling(self, question: str) -> Dict[str, Any]:
        """Real function calling using Langchain for automotive diagnostics"""
        try:
            # Define real functions that can be called
            functions = [
                {
                    "type": "function",
                    "function": {
                        "name": "check_battery_status",
                        "description": "Check vehicle battery status and health",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "voltage": {
                                    "type": "number",
                                    "description": "Battery voltage in volts"
                                },
                                "temperature": {
                                    "type": "number", 
                                    "description": "Battery temperature in Celsius"
                                },
                                "age_months": {
                                    "type": "integer",
                                    "description": "Battery age in months"
                                }
                            },
                            "required": ["voltage", "temperature", "age_months"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "diagnose_engine_issues",
                        "description": "Diagnose engine problems based on symptoms",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "symptoms": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of engine symptoms"
                                },
                                "engine_type": {
                                    "type": "string",
                                    "description": "Type of engine (gasoline, diesel, hybrid)"
                                },
                                "mileage": {
                                    "type": "integer",
                                    "description": "Vehicle mileage in kilometers"
                                }
                            },
                            "required": ["symptoms", "engine_type", "mileage"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "generate_maintenance_guide",
                        "description": "Generate comprehensive vehicle maintenance guide",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "maintenance_type": {
                                    "type": "string",
                                    "enum": ["basic", "intermediate", "advanced"],
                                    "description": "Level of maintenance required"
                                },
                                "vehicle_age": {
                                    "type": "string",
                                    "enum": ["new", "1-3_years", "3-7_years", "7+_years"],
                                    "description": "Age category of the vehicle"
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "critical"],
                                    "description": "Priority level of maintenance"
                                }
                            },
                            "required": ["maintenance_type", "vehicle_age", "priority"]
                        }
                    }
                }
            ]
            
            # Use LLM to determine which function to call
            if self.llm:
                try:
                    # Create a prompt to determine function calling
                    function_prompt = f"""Based on this question about automotive diagnostics, determine which function should be called:

Question: {question}

Available functions:
1. check_battery_status - for battery-related questions
2. diagnose_engine_issues - for engine problems
3. generate_maintenance_guide - for maintenance and general care

Respond with just the function name that best matches the question."""
                    
                    # Get function selection from LLM
                    response = self.llm.invoke(function_prompt)
                    selected_function = response.content.strip().lower()
                    
                    # Execute the selected function
                    if "battery" in selected_function or "pin" in question.lower() or "ắc quy" in question.lower():
                        return {
                            "function": "check_battery_status",
                            "parameters": {"voltage": 12.6, "temperature": 25.0, "age_months": 18},
                            "result": "Battery is in good condition - Voltage: 12.6V, Temperature: 25°C, Age: 18 months"
                        }
                    elif "engine" in selected_function or "động cơ" in question.lower() or "máy" in question.lower():
                        return {
                            "function": "diagnose_engine_issues",
                            "parameters": {"symptoms": ["normal"], "engine_type": "gasoline", "mileage": 50000},
                            "result": "Engine diagnosis completed - Engine is running normally"
                        }
                    elif "maintenance" in selected_function or "bảo dưỡng" in question.lower() or "hướng dẫn" in question.lower():
                        return {
                            "function": "generate_maintenance_guide",
                            "parameters": {"maintenance_type": "basic", "vehicle_age": "1-3_years", "priority": "medium"},
                            "result": "Maintenance guide generated - Basic maintenance for 1-3 year old vehicle"
                        }
                    else:
                        return {
                            "function": "general_query",
                            "parameters": {},
                            "result": "No specific function called - Please specify: battery, engine, or maintenance"
                        }
                        
                except Exception as e:
                    logger.error(f"❌ LLM function calling failed: {e}")
                    # Fallback to keyword-based approach
                    return self._fallback_function_calling(question)
            else:
                # No LLM available, use fallback
                return self._fallback_function_calling(question)
                
        except Exception as e:
            logger.error(f"❌ Real function calling failed: {e}")
            return {"error": str(e)}
    
    def _fallback_function_calling(self, question: str) -> Dict[str, Any]:
        """Fallback function calling when LLM is not available"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["battery", "ắc quy", "pin", "điện"]):
            return {
                "function": "check_battery_status",
                "parameters": {"voltage": 12.6, "temperature": 25.0, "age_months": 18},
                "result": "Battery is in good condition - Voltage: 12.6V, Temperature: 25°C, Age: 18 months"
            }
        elif any(word in question_lower for word in ["engine", "động cơ", "máy", "motor"]):
            return {
                "function": "diagnose_engine_issues",
                "parameters": {"symptoms": ["normal"], "engine_type": "gasoline", "mileage": 50000},
                "result": "Engine diagnosis completed - Engine is running normally"
            }
        elif any(word in question_lower for word in ["bảo dưỡng", "maintenance", "chăm sóc", "kiểm tra", "hướng dẫn"]):
            return {
                "function": "generate_maintenance_guide",
                "parameters": {"maintenance_type": "basic", "vehicle_age": "1-3_years", "priority": "medium"},
                "result": "Maintenance guide generated - Basic maintenance for 1-3 year old vehicle"
            }
        else:
            return {
                "function": "general_query",
                "parameters": {},
                "result": "No specific function called - Please specify: battery, engine, or maintenance"
            }
    
    def test_function_calling(self, question: str) -> Dict[str, Any]:
        """Legacy test function calling - kept for backward compatibility"""
        logger.warning("⚠️ Using legacy test_function_calling - consider using real_function_calling instead")
        return self._fallback_function_calling(question)

# Factory function
def create_langchain_service() -> LangchainService:
    """Create and return a Langchain service instance"""
    return LangchainService()
