from typing import Dict, Union, List
import re

class ConstantLookup:
    def __init__(self, constants: Dict[str, float]):
        self.constants = constants
        self.constant_descriptions = {
            'c': 'Speed of light in vacuum',
            'g': 'Acceleration due to gravity on Earth',
            'h': "Planck's constant",
            'k': "Boltzmann's constant",
            'e': 'Elementary charge',
            'm_e': 'Electron mass',
            'm_p': 'Proton mass',
            'N_A': "Avogadro's number",
            'R': 'Gas constant',
            'epsilon_0': 'Vacuum permittivity',
            'mu_0': 'Vacuum permeability'
        }
    
    def lookup(self, query: str) -> Union[str, Dict[str, Union[float, str]]]:
        """Look up a physical constant and return its value and description."""
        query = query.lower().strip()
        
        # First try exact symbol match
        if query in self.constants:
            return {
                'symbol': query,
                'value': self.constants[query],
                'description': self.constant_descriptions[query],
                'unit': self._get_unit(query)
            }
        
        # Then try exact description match
        for symbol, desc in self.constant_descriptions.items():
            if desc.lower() == query:
                return {
                    'symbol': symbol,
                    'value': self.constants[symbol],
                    'description': desc,
                    'unit': self._get_unit(symbol)
                }
        
        # Finally try partial matches
        matches = []
        for symbol, desc in self.constant_descriptions.items():
            # Check if query is in description or vice versa
            if (query in desc.lower() or 
                desc.lower() in query or 
                symbol.lower() in query):
                matches.append({
                    'symbol': symbol,
                    'value': self.constants[symbol],
                    'description': desc,
                    'unit': self._get_unit(symbol),
                    'match_score': self._calculate_match_score(query, symbol, desc)
                })
        
        if not matches:
            return "No matching physical constants found"
        
        # Sort matches by score and return the best match
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        best_match = matches[0]
        # Remove the match_score from the result
        best_match.pop('match_score', None)
        return best_match
    
    def _calculate_match_score(self, query: str, symbol: str, description: str) -> float:
        """Calculate how well a constant matches the query."""
        score = 0.0
        query = query.lower()
        symbol = symbol.lower()
        description = description.lower()
        
        # Exact matches get highest scores
        if query == symbol:
            score += 100
        if query == description:
            score += 100
            
        # Symbol matches get higher scores than description matches
        if symbol in query or query in symbol:
            score += 50
            
        # Description matches
        if description in query or query in description:
            score += 25
            
        # Partial word matches
        query_words = set(re.findall(r'\w+', query))
        desc_words = set(re.findall(r'\w+', description))
        common_words = query_words.intersection(desc_words)
        score += len(common_words) * 10
        
        return score
    
    def _get_unit(self, symbol: str) -> str:
        """Get the SI unit for a physical constant."""
        units = {
            'c': 'm/s',
            'g': 'm/s^2',
            'h': 'J*s',
            'k': 'J/K',
            'e': 'C',
            'm_e': 'kg',
            'm_p': 'kg',
            'N_A': 'mol^-1',
            'R': 'J/(mol*K)',
            'epsilon_0': 'F/m',
            'mu_0': 'H/m'
        }
        return units.get(symbol, 'dimensionless')