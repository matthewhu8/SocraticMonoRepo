from typing import Dict, List, Optional
from .llm_client import call_llm
import re
import random
import time
import json
from enum import Enum
import logging
from .session import StudentSession

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueryType(Enum):
    HIDDEN_VALUE_REQUEST = "hidden_value_request"
    FORMULA_REQUEST = "formula_request"
    ANSWER_REQUEST = "answer_request"
    HINT_REQUEST = "hint_request"
    GENERAL_QUESTION = "general_question"
    OFF_TOPIC = "off_topic"
    ANSWER_ATTEMPT = "answer_attempt"


class ConversationService:
    def __init__(self, call_llm: call_llm, session_store=None):
        self.llm_call = call_llm
        self.sessions = {}  # In-memory session store
        self.session_store = session_store  # External session store (optional)
        
        # Common patterns for query classification
        self.value_patterns = [
            r"^\s*([a-zA-Z0-9_]+)[\?\.]?\s*$",  # exactly "x" or "x?"
            r"(?i)(?:what(?:'s|\s+(?:is|are))?\s+)(?:the\s+value\s+of\s+)?([a-zA-Z0-9_]+)[\?\.]?",
            r"(?i)(?:can|could)\s+you\s+(?:tell\s+me\s+|let\s+me\s+know\s+)?(?:what(?:'s|\s+(?:is|are))?\s+)?(?:the\s+value\s+of\s+)?([a-zA-Z0-9_]+)[\?\.]?",
            r"(?i)(?:tell|give|let)\s+me\s+(?:know\s+)?(?:what\s+)?([a-zA-Z0-9_]+)(?:\s+is)?[\?\.]?"
        ]

        # Patterns to detect answer attempts (extracting a number)
        self.answer_attempt_patterns = [
            r"(?i).*?\b(?:is\s+the\s+answer|the\s+solution\s+is|result\s+is)\s*(\d+(?:\.\d+)?)\b",
            r"(?i)^\s*(\d+(?:\.\d+)?)\s*\??$"  # Covers queries like "13" or "13?"
        ]
        
        self.formula_patterns = [
            r"(?i)formula",
            r"(?i)equation",
            r"(?i)how\s+do\s+I\s+(?:solve|calculate|compute|find)",
            r"(?i)what\s+(?:formula|equation)\s+(?:should|do|can|could|would)\s+I\s+use"
        ]
        
        self.answer_patterns = [
            r"(?i)(?:what(?:'s|\s+is))?\s+the\s+answer",
            r"(?i)solve\s+(?:this|the\s+problem)",
            r"(?i)(?:tell|give)\s+me\s+the\s+answer",
            r"(?i)solution",
            r"(?i)result",
            r"(?i)final\s+(?:answer|result|value)"
        ]
        
        self.hint_patterns = [
            r"(?i)(?:can|could)\s+(?:I\s+(?:get|have)|you\s+give\s+me)\s+a\s+hint",
            r"(?i)hint",
            r"(?i)help\s+me",
            r"(?i)I(?:'m|\s+am)\s+stuck",
            r"(?i)(?:how|where)\s+(?:do|should)\s+I\s+start",
            r"(?i)what\s+(?:should|do)\s+I\s+do\s+next"
        ]
    
    def get_or_create_session(self, user_id: str, problem_id: int) -> StudentSession:
        """Get existing session or create a new one"""
        print("get_or_create_session called")
        session_id = f"{user_id}_{problem_id}"
        
        # Try to get from memory
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try to get from external store
        if self.session_store:
            session_data = self.session_store.get_session(session_id)
            if session_data:
                session = StudentSession.from_dict(session_data)
                self.sessions[session_id] = session
                return session
        
        # Create new session
        session = StudentSession(problem_id)
        self.sessions[session_id] = session
        return session
    
    def save_session(self, user_id: str, session: StudentSession):
        """Save session to external store if available"""
        session_id = f"{user_id}_{session.problem_id}"
        self.sessions[session_id] = session
        
        if self.session_store:
            self.session_store.save_session(session_id, session.to_dict())
    
    def classify_query(self, query: str, hidden_values: Dict) -> tuple[QueryType, Optional[str]]:
        """Classify the type of query and extract any referenced variable"""
        print("classify_query called")
        query = query.strip().lower()

        # First, check for answer attempts with an embedded number
        for pattern in self.answer_attempt_patterns:
            match = re.search(pattern, query)
            if match and len(match.groups()) > 0:
                return QueryType.ANSWER_ATTEMPT, None
        
        # Check for hidden value requests
        for pattern in self.value_patterns:
            matches = re.search(pattern, query)
            if matches and len(matches.groups()) > 0:
                var_name = matches.group(1).lower()
                # Check if this variable exists in hidden_values
                for key in hidden_values.keys():
                    if key.lower() == var_name:
                        return QueryType.HIDDEN_VALUE_REQUEST, key
        
        # Check for formula requests
        for pattern in self.formula_patterns:
            if re.search(pattern, query):
                return QueryType.FORMULA_REQUEST, None
        
        # Check for direct answer requests
        for pattern in self.answer_patterns:
            if re.search(pattern, query):
                return QueryType.ANSWER_REQUEST, None
        
        # Check for hint requests
        for pattern in self.hint_patterns:
            if re.search(pattern, query):
                return QueryType.HINT_REQUEST, None
        
        # Default to general question
        return QueryType.GENERAL_QUESTION, None
    

    def process_query(self, user_query: str, problem_id: int, user_id: str = "anonymous", test_code: str = None, question_index: int = None) -> str:
        """
        Process a user query and return a response
        
        Args:
            user_query: The user's question
            problem_id: ID of the problem (used for standalone problems)
            user_id: User identifier for session management
            test_code: Optional test code for test questions
            question_index: Optional question index for test questions
        
        Returns:
            str: AI response to the user's query
        """
        logger.info(f"Processing query: {user_query} for problem {problem_id}, test_code: {test_code}, question_index: {question_index}")
        
        # Retrieve problem metadata (will use test_code and question_index if provided)
        metadata = self.retrieve_problem_metadata(problem_id, test_code, question_index)
        mode = metadata.get("hint_level", "medium")  # default to practice if not defined
        hidden_values = metadata.get("hidden_values", {})
        formula = metadata.get("formula", "")
        expected_answer = metadata.get("answer", None)
        
        # Generate a unique session ID that includes test context if present
        if test_code and question_index is not None:
            session_id = f"{user_id}_{test_code}_{question_index}"
        else:
            session_id = f"{user_id}_{problem_id}"
        
        session = self.get_or_create_session(session_id, problem_id)

        query_type, var_name = self.classify_query(user_query, hidden_values)
        logger.info(f"Query classified as: {query_type}, var_name: {var_name}")
        
        response = ""
        prompt = ""
        
        if query_type == QueryType.ANSWER_ATTEMPT:
            # Handle answer attempt; for testing mode, give binary feedback
            try:
                user_answer = float(re.search(r"\d+(?:\.\d+)?", user_query).group())
            except Exception:
                user_answer = None
            
            if user_answer is not None and expected_answer is not None:
                correct = abs(user_answer - float(expected_answer)) < 1e-6
                if mode == "hard":
                    response = "Correct!" if correct else "Incorrect."
                else:  # for practice or learning
                    response = "That's correct! Well done." if correct \
                        else "That doesn't seem to be correct. Please review your steps and try again."
            else:
                response = "I couldn't understand your answer. Could you please try again?"
        
        elif query_type == QueryType.HIDDEN_VALUE_REQUEST and var_name:
            if var_name in hidden_values:
                time.sleep(random.uniform(0.5, 1.5))
                session.reveal_value(var_name)
                response = f"The value of {var_name} is {hidden_values[var_name]}."
        
        elif query_type == QueryType.FORMULA_REQUEST:
            if mode == "hard":
                response = "Formula is not available in testing mode."
            else:
                if len(session.revealed_values) >= len(hidden_values) * 0.5:
                    session.reveal_formula()
                    response = f"You can use the formula: {formula}"
                else:
                    prompt = self.build_formula_hint_prompt(metadata, session, user_query)
                    response = self.llm_call(prompt)
        
        elif query_type == QueryType.ANSWER_REQUEST:
            if mode == "hard":
                response = "Answer feedback is disabled in testing mode."
            else:
                if len(session.revealed_values) >= len(hidden_values) * 0.75 and session.formula_revealed:
                    prompt = self.build_guided_solution_prompt(metadata, session, user_query)
                    response = self.llm_call(prompt)
                else:
                    prompt = self.build_answer_redirect_prompt(metadata, session, user_query)
                    response = self.llm_call(prompt)
        
        else:  # HINT_REQUEST or GENERAL_QUESTION
            if mode == "hard":
                response = "Hints are not available in testing mode."
            else:
                if query_type == QueryType.HINT_REQUEST:
                    session.increase_hint_level()
                    # In learning mode you might increase the hint level more or tailor the prompt differently
                    if mode == "easy":
                        # Optionally adjust the prompt to be more detailed here
                        pass
                prompt = self.build_augmented_prompt(metadata, session, user_query)
                response = self.llm_call(prompt)
        
        session.add_interaction(user_query, response)
        self.save_session(user_id, session)
        self.afterResponse(response, prompt if 'prompt' in locals() else "Direct response", problem_id)
        return response
    
    def build_augmented_prompt(self, metadata: Dict, session: StudentSession, user_query: str) -> str:
        """Build a comprehensive prompt with all context for the LLM"""
        public_question = metadata.get("public_question", "")
        hidden_values = metadata.get("hidden_values", {})
        teacher_instructions = metadata.get("teacher_instructions", "")
        formula = metadata.get("formula", "")
        
        # Get appropriate examples based on session state
        examples = self.get_examples_for_state(session)
        
        # Format revealed values
        revealed_values_str = "None yet" if not session.revealed_values else ", ".join([f"{key}: {hidden_values[key]}" for key in session.revealed_values if key in hidden_values])
        
        # Build conversation history context (limited to last 5 exchanges)
        history = ""
        if session.conversation_history:
            history_items = session.conversation_history[-10:]  # Last 5 exchanges (10 messages)
            for item in history_items:
                role = "Student" if item["role"] == "student" else "Tutor"
                history += f"{role}: {item['content']}\n"
        
        # Determine appropriate hint level instruction
        hint_instruction = self.get_hint_level_instruction(session.hint_level, len(hidden_values), len(session.revealed_values))
        
        prompt = f"""
[SYSTEM]
You are a Socratic tutor for a mathematics problem. Your goal is to guide students to discover answers themselves through questioning and progressive hints.

PROBLEM CONTEXT:
- Public Question: {public_question}
- Variables the student knows: {revealed_values_str}
- Formula has been revealed: {"Yes" if session.formula_revealed else "No"}
{f"- Formula: {formula}" if session.formula_revealed else ""}
- Student attempt count: {session.attempt_count}

TEACHER INSTRUCTIONS:
{teacher_instructions}

YOUR GUIDELINES:
1. Never directly solve the problem unless the student has discovered at least 75% of the variables and the formula.
2. When students are stuck, offer progressively more specific hints.
3. Celebrate small victories when students discover key insights.
4. Ask leading questions that direct students toward the next step.
5. {hint_instruction}
6. Keep responses concise and focused on the current step.

[EXAMPLES]
{examples}
[/EXAMPLES]

[CONVERSATION HISTORY]
{history}
[/CONVERSATION HISTORY]

[STUDENT QUERY]
{user_query}
[/STUDENT QUERY]
"""
        
        logger.debug(f"Built prompt: {prompt}")
        return prompt
    
    def build_formula_hint_prompt(self, metadata: Dict, session: StudentSession, user_query: str) -> str:
        """Build a prompt specifically for hinting at the formula without revealing it fully"""
        basic_prompt = self.build_augmented_prompt(metadata, session, user_query)
        
        # Add specific instructions for formula hinting
        formula_hint_instruction = f"""
ADDITIONAL INSTRUCTIONS:
The student is asking about the formula, but has only discovered {len(session.revealed_values)} out of {len(metadata.get('hidden_values', {}))} variables.
Don't reveal the complete formula yet. Instead:
1. Acknowledge they need a formula
2. Mention what type of formula might be useful based on the problem context
3. Ask if they can identify any more variables they might need
4. If appropriate, give a partial form of the formula with placeholders

Remember to be encouraging and supportive while guiding them to discover more on their own.
"""
        
        return basic_prompt + formula_hint_instruction
    
    def build_guided_solution_prompt(self, metadata: Dict, session: StudentSession, user_query: str) -> str:
        """Build a prompt for guiding students through the solution when they've done enough work"""
        basic_prompt = self.build_augmented_prompt(metadata, session, user_query)
        
        solution_instruction = f"""
ADDITIONAL INSTRUCTIONS:
The student has discovered {len(session.revealed_values)} out of {len(metadata.get('hidden_values', {}))} variables and knows the formula.
They are ready for more direct guidance. Please:
1. Acknowledge their progress
2. Review the formula and the known variables
3. Guide them through substituting the values
4. Ask them to attempt the calculation
5. Be ready to confirm if their answer is correct, but let them do the actual calculation

Don't solve it completely for them, but provide a clear path to the solution.
"""
        
        return basic_prompt + solution_instruction
    
    def build_answer_redirect_prompt(self, metadata: Dict, session: StudentSession, user_query: str) -> str:
        """Build a prompt for redirecting students who ask for the answer too early"""
        basic_prompt = self.build_augmented_prompt(metadata, session, user_query)
        
        redirect_instruction = f"""
ADDITIONAL INSTRUCTIONS:
The student is asking for the answer directly, but has only discovered {len(session.revealed_values)} out of {len(metadata.get('hidden_values', {}))} variables and {'knows' if session.formula_revealed else 'does not know'} the formula.

Please redirect them without being negative:
1. Acknowledge their desire for the answer
2. Remind them that understanding the process is important
3. Point out what they've discovered so far
4. Suggest a specific next step (e.g., "Have you tried finding out what [specific variable] is?")
5. Encourage them that they're making progress

Be supportive and guiding rather than scolding.
"""
        
        return basic_prompt + redirect_instruction
    
    def get_examples_for_state(self, session: StudentSession) -> str:
        """Return appropriate examples based on the current session state"""
        # This would ideally come from a database of curated examples
        # Here we'll just return some static examples based on session state
        
        if len(session.revealed_values) == 0:
            # Beginning stage examples
            return """Student: I don't know where to start.
Tutor: Let's think about what information we need. What variables do you think might be relevant to this problem?

Student: What is x?
Tutor: The value of x is 3.
"""
        elif session.formula_revealed:
            # Formula stage examples
            return """Student: How do I use this formula?
Tutor: Look at the formula and consider which values you know. Which variables can you substitute right away?

Student: I think I need to put the values into the formula.
Tutor: That's right! Try substituting x=3 and y=10 into the formula and see what you get.
"""
        else:
            # Middle stage examples
            return """Student: What else do I need to know?
Tutor: You've discovered x=3. What other variables do you think might be in the equation? The problem is asking for x+y, so what else might you need?

Student: I'm not sure what formula to use.
Tutor: For this problem, think about what operation the question is asking you to perform. The problem asks for "x + y", so what mathematical operation does that suggest?
"""
    
    def get_hint_level_instruction(self, hint_level: int, total_vars: int, revealed_vars: int) -> str:
        """Return a hint instruction based on the current hint level"""
        if hint_level == 0:
            return "Start with very general hints that encourage exploration."
        elif hint_level == 1:
            return "Suggest looking for specific variables that haven't been discovered yet."
        elif hint_level == 2:
            return f"Point out that they've found {revealed_vars} of {total_vars} variables and need to find more."
        elif hint_level == 3:
            return "If they're stuck, suggest the type of formula that might be useful."
        elif hint_level == 4:
            return "Provide more direct guidance on the next specific step they should take."
        else:  # hint_level >= 5
            return "Give very explicit directions while still requiring them to do the calculations."
    
    def retrieve_problem_metadata(self, problem_id: int, test_code: str = None, question_index: int = None) -> Dict:
        logger.info(f"Retrieving metadata for problem_id: {problem_id}, test_code: {test_code}, question_index: {question_index}")
        
        # If test_code and question_index are provided, this is a test question
        if test_code and question_index is not None:
            # Fix imports - use absolute paths instead of relative
            from sqlalchemy.orm import Session
            # Import with proper absolute path
            from ...db.database import SessionLocal
            from ...Modules.Problem.problem_service import ProblemService
            
            # Get database session
            db = SessionLocal()
            try:
                # Get problem service
                problem_service = ProblemService()
                
                # Get the specific question from the test
                question = problem_service.get_test_question(db, test_code, question_index)
                if question:
                    # Check for both naming conventions
                    public_question = question.get("public_question") or question.get("publicQuestion")
                    hidden_values = question.get("hidden_values") or question.get("hiddenValues", {})
                    formula = question.get("formula", "")
                    answer = question.get("answer")
                    teacher_instructions = question.get("teacher_instructions") or question.get("teacherInstructions", "")
                    hint_level = question.get("hint_level") or question.get("hintLevel", "easy")
                    subject = question.get("subject", "")
                    topic = question.get("topic", "")
                    
                    # Transform the question data structure to match metadata format
                    metadata = {
                        "public_question": public_question, 
                        "hidden_values": hidden_values,
                        "formula": formula,
                        "answer": answer,
                        "teacher_instructions": teacher_instructions,
                        "hint_level": hint_level,
                        "subject": subject,
                        "topic": topic
                    }
                    return metadata
            finally:
                db.close()
        
    
    def afterResponse(self, response: str, prompt: str, problem_id: int) -> None:
        """Log the interaction for analysis"""
        logger.info(f"Generated response for problem {problem_id}: {response[:50]}...")
        
        # This would typically log to a database or analytics system
        # For now, just logging to console
        try:
            # Add any additional logging or analytics here
            pass
        except Exception as e:
            logger.error(f"Error in afterResponse: {str(e)}")