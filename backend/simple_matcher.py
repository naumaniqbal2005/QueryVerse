import sqlite3
import re
from difflib import SequenceMatcher
import spacy

class SimpleNameMatcher:
    def __init__(self, db_path="mydb.db"):
        self.db_path = db_path
        self.games = []
        self.users = []
        # Load spacy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("Spacy NLP model loaded successfully")
        except OSError:
            print("Warning: Spacy model not found, using basic pattern matching")
            self.nlp = None
        self.load_data()
    
    def load_data(self):
        """Load exact names from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load games
        cursor.execute("SELECT GameTitle FROM Games")
        self.games = [row[0] for row in cursor.fetchall()]
        
        # Load users
        cursor.execute("SELECT FullName FROM Users")
        self.users = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        print(f"Loaded {len(self.games)} games and {len(self.users)} users")
    
    def find_match(self, query_text, threshold=0.6):
        """Find best match using simple string similarity"""
        best_match = None
        best_score = 0.0
        
        query_lower = query_text.lower()
        
        # Check games
        for game in self.games:
            game_lower = game.lower()
            # Calculate similarity ratio (case-insensitive)
            matcher = SequenceMatcher(None, query_lower, game_lower)
            ratio = matcher.ratio()
            
            if ratio > threshold and ratio > best_score:
                best_match = ("game", game, ratio)
                best_score = ratio
        
        # Check users
        for user in self.users:
            user_lower = user.lower()
            # Calculate similarity ratio (case-insensitive)
            matcher = SequenceMatcher(None, query_lower, user_lower)
            ratio = matcher.ratio()
            
            if ratio > threshold and ratio > best_score:
                best_match = ("user", user, ratio)
                best_score = ratio
        
        return best_match
    
    def extract_names(self, query):
        """Extract person names and game titles using spacy or fallback regex"""
        names = []
        
        if self.nlp:
            # Use spacy for named entity recognition
            doc = self.nlp(query)
            # Extract PERSON entities
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    names.append(ent.text)
                # Also look for potential game titles (proper nouns)
                elif ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"]:
                    names.append(ent.text)
        
        # Fallback: use regex patterns for both capitalized and lowercase
        # Multi-word phrases (both cases)
        multi_word_cap = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        multi_word_lower = re.findall(r'\b[a-z]+\s+[a-z]+\b', query)
        
        # Single words (both cases)
        single_cap = re.findall(r'\b[A-Z][a-z]+\b', query)
        single_lower = re.findall(r'\b[a-z]{3,}\b', query)
        
        names.extend(multi_word_cap)
        names.extend(single_cap)
        
        # For lowercase, be more selective - look for patterns that suggest names
        # Common stop words to filter out (universal English words)
        stop_words = {'has', 'have', 'had', 'was', 'were', 'been', 'will', 'would', 'could', 'should', 
                      'may', 'might', 'must', 'can', 'shall', 'does', 'did', 'do', 'is', 'are', 'am',
                      'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                      'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above',
                      'below', 'between', 'under', 'along', 'following', 'across', 'behind', 'beyond',
                      'plus', 'except', 'nor', 'yet', 'so', 'since', 'unless', 'until', 'while',
                      'where', 'when', 'how', 'what', 'which', 'who', 'whom', 'whose', 'why', 'whether',
                      'show', 'find', 'get', 'give', 'tell', 'ask', 'work', 'seem', 'feel', 'try', 'leave',
                      'call', 'ever', 'any', 'all', 'both', 'each', 'few', 'many', 'most', 'other', 'some', 'such',
                      'this', 'that', 'these', 'those', 'there', 'their', 'they', 'them', 'then', 'than'}
        
        # Add lowercase multi-word combinations
        for name in multi_word_lower:
            words = name.split()
            # Skip if any word is a stop word
            if not any(word in stop_words for word in words):
                names.append(name)
        
        # Add lowercase single words that aren't stop words
        for word in single_lower:
            if word not in stop_words:
                names.append(word)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        
        return unique_names
    
    def enhance_query(self, query):
        """Enhance query with exact matches only"""
        enhanced_query = query
        
        # Extract potential names using improved method
        potential_names = self.extract_names(query)
        print(f"Potential names: {potential_names}")
        for name in potential_names:
            match = self.find_match(name, threshold=0.7)
            if match:
                match_type, exact_name, similarity = match
                # Only replace if it's a meaningful improvement
                if name != exact_name:
                    enhanced_query = enhanced_query.replace(name, f'"{exact_name}"')
                    print(f"Replaced '{name}' with '{exact_name}' (similarity: {similarity:.2f})")
        
        return enhanced_query

# Initialize matcher
name_matcher = SimpleNameMatcher()
