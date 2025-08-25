#!/usr/bin/env python3
"""
AI Tools LLM Proxy Health Checker

A standalone health check tool for testing all three providers (OpenAI, Anthropic, Opensource)
with student authentication and token management capabilities.

Usage:
    python health_checker.py --username USERNAME --pin PIN [options]
    
Options:
    -v, --verbose       Show detailed JSON responses
    --show-token        Display the JWT token after registration
    --token-only        Only register and show token, skip health checks
    --provider PROVIDER Test only specific provider (openai, anthropic, opensource)
    --username USERNAME Username for authentication (required if not in .env)
    --pin PIN           PIN for authentication (required if not in .env)
    --help              Show this help message
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, Optional, List
import httpx
from dotenv import load_dotenv

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text: str, color: str = Colors.WHITE) -> None:
    """Print colored text to terminal."""
    print(f"{color}{text}{Colors.END}")

def print_header(text: str) -> None:
    """Print a formatted header."""
    print_colored(f"\n{Colors.BOLD}{'='*60}", Colors.CYAN)
    print_colored(f"{text.center(60)}", Colors.CYAN + Colors.BOLD)
    print_colored(f"{'='*60}{Colors.END}", Colors.CYAN)

def print_status(provider: str, status: str, details: str = "") -> None:
    """Print provider status with color coding."""
    color = Colors.GREEN if status == "PASS" else Colors.RED
    status_text = f"[{status}]".ljust(8)
    provider_text = provider.ljust(12)
    print_colored(f"{provider_text} {status_text} {details}", color)

class HealthChecker:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.jwt_token: Optional[str] = None
        self.client = httpx.Client(timeout=config.get('PROXY_TIMEOUT', 30))
        
    def register_user(self, username: str, pin: str) -> bool:
        """Register user and obtain JWT token."""
        try:
            response = self.client.post(
                f"{self.config['PROXY_BASE_URL']}/auth/register",
                json={"username": username, "pin": pin}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get('token')
                if self.jwt_token:
                    print_colored(f"✓ Registration successful for user: {username}", Colors.GREEN)
                    return True
                else:
                    print_colored("✗ Registration failed: No token received", Colors.RED)
                    return False
            else:
                print_colored(f"✗ Registration failed: {response.status_code} - {response.text}", Colors.RED)
                return False
                
        except Exception as e:
            print_colored(f"✗ Registration error: {e}", Colors.RED)
            return False
    
    def test_opensource_provider(self, verbose: bool = False) -> Dict[str, Any]:
        """Test the opensource provider."""
        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "openai--gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "Say 'Health check successful' and nothing else."}
                ],
                "max_tokens": 10,
                "stream": False
            }
            
            response = self.client.post(
                f"{self.config['PROXY_BASE_URL']}/opensource/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            result = {
                "provider": "opensource",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time": response.elapsed.total_seconds(),
                "error": None,
                "response_data": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["response_data"] = data
                if verbose:
                    result["full_response"] = data
            else:
                result["error"] = response.text
                
            return result
            
        except Exception as e:
            return {
                "provider": "opensource",
                "status_code": 0,
                "success": False,
                "response_time": 0,
                "error": str(e),
                "response_data": None
            }
    
    def test_openai_provider(self, verbose: bool = False) -> Dict[str, Any]:
        """Test the OpenAI provider."""
        if not self.config.get('OPENAI_API_KEY') or self.config['OPENAI_API_KEY'] == 'your_openai_api_key_here':
            return {
                "provider": "openai",
                "status_code": 0,
                "success": False,
                "response_time": 0,
                "error": "OpenAI API key not configured",
                "response_data": None
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json",
                "X-User-OpenAI-Key": self.config['OPENAI_API_KEY']
            }
            
            if self.config.get('OPENAI_ORG_ID') and self.config['OPENAI_ORG_ID'] != 'your_openai_org_id_here':
                headers["X-User-OpenAI-Org"] = self.config['OPENAI_ORG_ID']
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Say 'Health check successful' and nothing else."}
                ],
                "max_tokens": 10,
                "stream": False
            }
            
            response = self.client.post(
                f"{self.config['PROXY_BASE_URL']}/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            result = {
                "provider": "openai",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time": response.elapsed.total_seconds(),
                "error": None,
                "response_data": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["response_data"] = data
                if verbose:
                    result["full_response"] = data
            else:
                result["error"] = response.text
                
            return result
            
        except Exception as e:
            return {
                "provider": "openai",
                "status_code": 0,
                "success": False,
                "response_time": 0,
                "error": str(e),
                "response_data": None
            }
    
    def test_anthropic_provider(self, verbose: bool = False) -> Dict[str, Any]:
        """Test the Anthropic provider."""
        if not self.config.get('ANTHROPIC_API_KEY') or self.config['ANTHROPIC_API_KEY'] == 'your_anthropic_api_key_here':
            return {
                "provider": "anthropic",
                "status_code": 0,
                "success": False,
                "response_time": 0,
                "error": "Anthropic API key not configured",
                "response_data": None
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json",
                "X-User-Anthropic-Key": self.config['ANTHROPIC_API_KEY']
            }
            
            payload = {
                "model": "claude-3-haiku-20240307",
                "messages": [
                    {"role": "user", "content": "Say 'Health check successful' and nothing else."}
                ],
                "max_tokens": 10,
                "stream": False
            }
            
            response = self.client.post(
                f"{self.config['PROXY_BASE_URL']}/anthropic/v1/messages",
                headers=headers,
                json=payload
            )
            
            result = {
                "provider": "anthropic",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time": response.elapsed.total_seconds(),
                "error": None,
                "response_data": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["response_data"] = data
                if verbose:
                    result["full_response"] = data
            else:
                result["error"] = response.text
                
            return result
            
        except Exception as e:
            return {
                "provider": "anthropic",
                "status_code": 0,
                "success": False,
                "response_time": 0,
                "error": str(e),
                "response_data": None
            }
    
    def run_health_checks(self, providers: List[str], verbose: bool = False) -> Dict[str, Any]:
        """Run health checks for specified providers."""
        results = {}
        
        provider_tests = {
            "opensource": self.test_opensource_provider,
            "openai": self.test_openai_provider,
            "anthropic": self.test_anthropic_provider
        }
        
        for provider in providers:
            if provider in provider_tests:
                print_colored(f"\nTesting {provider} provider...", Colors.BLUE)
                result = provider_tests[provider](verbose)
                results[provider] = result
                
                # Print status
                status = "PASS" if result["success"] else "FAIL"
                details = f"({result['response_time']:.2f}s)" if result["success"] else f"Error: {result['error']}"
                print_status(provider.capitalize(), status, details)
                
                # Print verbose output if requested
                if verbose and result.get("full_response"):
                    print_colored(f"\nDetailed response for {provider}:", Colors.YELLOW)
                    print(json.dumps(result["full_response"], indent=2))
        
        return results
    
    def close(self):
        """Clean up resources."""
        self.client.close()

def load_config() -> Dict[str, Any]:
    """Load configuration from .env file."""
    # Load .env file from the health-checks directory
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    
    config = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'OPENAI_ORG_ID': os.getenv('OPENAI_ORG_ID'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'PROXY_BASE_URL': os.getenv('PROXY_BASE_URL', 'http://aitools.cs.vt.edu:7860'),
        'PROXY_TIMEOUT': int(os.getenv('PROXY_TIMEOUT', '30')),
        'DEFAULT_USERNAME': os.getenv('DEFAULT_USERNAME'),
        'DEFAULT_PIN': os.getenv('DEFAULT_PIN')
    }
    
    return config

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI Tools LLM Proxy Health Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python health_checker.py --username alice --pin 1234                    # Test opensource provider (default)
    python health_checker.py --username alice --pin 1234 -v                # Test opensource with verbose output
    python health_checker.py --username alice --pin 1234 --show-token      # Show JWT token after registration
    python health_checker.py --username alice --pin 1234 --token-only      # Only register and show token
    python health_checker.py --username alice --pin 1234 --provider openai # Test only OpenAI (requires API key)
    
    # If DEFAULT_USERNAME and DEFAULT_PIN are set in .env file:
    python health_checker.py                    # Uses credentials from .env file
    python health_checker.py -v                # Uses credentials from .env file with verbose output
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed JSON responses')
    parser.add_argument('--show-token', action='store_true',
                       help='Display the JWT token after registration')
    parser.add_argument('--token-only', action='store_true',
                       help='Only register and show token, skip health checks')
    parser.add_argument('--provider', choices=['openai', 'anthropic', 'opensource'],
                       help='Test only specific provider')
    parser.add_argument('--username', help='Username for authentication (required if not in .env)')
    parser.add_argument('--pin', help='PIN for authentication (required if not in .env)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Determine username and pin
    username = args.username or config['DEFAULT_USERNAME']
    pin = args.pin or config['DEFAULT_PIN']
    
    # Check if username and pin are available
    if not username:
        print_colored("Error: Username is required. Provide --username or set DEFAULT_USERNAME in .env file.", Colors.RED)
        return 1
    
    if not pin:
        print_colored("Error: PIN is required. Provide --pin or set DEFAULT_PIN in .env file.", Colors.RED)
        return 1
    
    # Determine which providers to test
    if args.provider:
        providers = [args.provider]
    else:
        providers = ['opensource']  # Default to opensource only for students
    
    # Initialize health checker
    checker = HealthChecker(config)
    
    try:
        print_header("AI Tools LLM Proxy Health Checker")
        print_colored(f"Proxy URL: {config['PROXY_BASE_URL']}", Colors.CYAN)
        print_colored(f"Username: {username}", Colors.CYAN)
        print_colored(f"Providers: {', '.join(providers)}", Colors.CYAN)
        
        # Register user
        print_colored(f"\nRegistering user '{username}'...", Colors.BLUE)
        if not checker.register_user(username, pin):
            print_colored("Registration failed. Cannot proceed with health checks.", Colors.RED)
            return 1
        
        # Show token if requested
        if args.show_token or args.token_only:
            print_colored(f"\nJWT Token:", Colors.YELLOW)
            print_colored(f"{checker.jwt_token}", Colors.WHITE)
        
        # Skip health checks if token-only mode
        if args.token_only:
            print_colored(f"\nToken-only mode: Skipping health checks.", Colors.YELLOW)
            return 0
        
        # Run health checks
        print_header("Health Check Results")
        results = checker.run_health_checks(providers, args.verbose)
        
        # Summary
        print_header("Summary")
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r["success"])
        failed_tests = total_tests - passed_tests
        
        print_colored(f"Total Tests: {total_tests}", Colors.CYAN)
        print_colored(f"Passed: {passed_tests}", Colors.GREEN)
        print_colored(f"Failed: {failed_tests}", Colors.RED if failed_tests > 0 else Colors.GREEN)
        
        # Return appropriate exit code
        return 0 if failed_tests == 0 else 1
        
    except KeyboardInterrupt:
        print_colored("\n\nHealth check interrupted by user.", Colors.YELLOW)
        return 1
    except Exception as e:
        print_colored(f"\nUnexpected error: {e}", Colors.RED)
        return 1
    finally:
        checker.close()

if __name__ == "__main__":
    sys.exit(main())
