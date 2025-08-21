# AI Tools LLM Proxy Health Checker

A standalone health check tool for testing all three providers (OpenAI, Anthropic, Opensource) with student authentication and token management capabilities.

## Setup

1. **Configure API Keys**: Edit the `.env` file in this directory with your API keys:
   ```bash
   # OpenAI Configuration
   OPENAI_API_KEY=your_actual_openai_api_key
   OPENAI_ORG_ID=your_openai_org_id  # Optional
   
   # Anthropic Configuration  
   ANTHROPIC_API_KEY=your_actual_anthropic_api_key
   ```

2. **Ensure Proxy Server is Running**: The health checker connects to the proxy server at `http://aitools.cs.vt.edu:7860` by default. For local testing, you can change `PROXY_BASE_URL` in the `.env` file to `http://localhost:7860` and run your local server:
   ```bash
   cd ..
   ./start.sh
   ```

## Usage

### Basic Usage

**Note**: Username and PIN are required either as command line arguments or set as `DEFAULT_USERNAME` and `DEFAULT_PIN` in the `.env` file.

```bash
# Test opensource provider (default - free for students)
python health_checker.py --username alice --pin 1234

# Test with verbose JSON output
python health_checker.py --username alice --pin 1234 -v

# Test specific providers (requires API keys for openai/anthropic)
python health_checker.py --username alice --pin 1234 --provider opensource
python health_checker.py --username alice --pin 1234 --provider openai
python health_checker.py --username alice --pin 1234 --provider anthropic

# If DEFAULT_USERNAME and DEFAULT_PIN are set in .env file:
python health_checker.py
python health_checker.py -v
```

### Authentication Options

```bash
# Show JWT token after registration
python health_checker.py --username alice --pin 1234 --show-token

# Only register and show token (skip health checks)
python health_checker.py --username alice --pin 1234 --token-only

# Use credentials from .env file (if DEFAULT_USERNAME and DEFAULT_PIN are set)
python health_checker.py --show-token
python health_checker.py --token-only
```

### Example Output

```
============================================================
            AI Tools LLM Proxy Health Checker            
============================================================
Proxy URL: http://aitools.cs.vt.edu:7860
Username: testuser
Providers: opensource, openai, anthropic

Registering user 'testuser'...
✓ Registration successful for user: testuser

============================================================
                    Health Check Results                   
============================================================

Testing opensource provider...
Opensource   [PASS]   (1.23s)

Testing openai provider...
OpenAI       [FAIL]   Error: OpenAI API key not configured

Testing anthropic provider...
Anthropic    [FAIL]   Error: Anthropic API key not configured

============================================================
                         Summary                          
============================================================
Total Tests: 3
Passed: 1
Failed: 2
```

## Configuration

The `.env` file supports the following configuration options:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ORG_ID=your_openai_org_id_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Proxy Server Configuration
PROXY_BASE_URL=http://aitools.cs.vt.edu:7860
PROXY_TIMEOUT=30

# Default Test Credentials
DEFAULT_USERNAME=testuser
DEFAULT_PIN=1234
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Show detailed JSON responses from providers |
| `--show-token` | Display the JWT token after registration |
| `--token-only` | Only register and show token, skip health checks |
| `--provider PROVIDER` | Test only specific provider (openai, anthropic, opensource) |
| `--username USERNAME` | Override default username |
| `--pin PIN` | Override default PIN |
| `--help` | Show help message |

## Educational Use

This tool is designed for educational environments where:

1. **Students need JWT tokens** for API access - use `--token-only` or `--show-token`
2. **Instructors need to verify connectivity** - run full health checks
3. **Different API keys are tested** - configure in `.env` file
4. **Individual provider testing** - use `--provider` option

## Troubleshooting

### Common Issues

1. **"Registration failed"**
   - Ensure the proxy server is running at the configured URL
   - Check that the username/PIN combination is valid

2. **"API key not configured"**
   - Edit the `.env` file with actual API keys
   - Remove placeholder values like `your_openai_api_key_here`

3. **Connection errors**
   - Verify `PROXY_BASE_URL` in `.env` matches your server
   - Check firewall settings if running on different machines

4. **Import errors**
   - Ensure you're using the same Python environment as the main proxy
   - Install dependencies: `pip install httpx python-dotenv`

### Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed or error occurred

## Examples

```bash
# Quick test of opensource provider (requires credentials)
python health_checker.py --username alice --pin 1234

# Detailed testing with token display
python health_checker.py --username alice --pin 1234 -v --show-token

# Test only OpenAI with custom credentials
python health_checker.py --provider openai --username student1 --pin 9876

# Get token for student use
python health_checker.py --token-only --username student2 --pin 1111

# If DEFAULT_USERNAME and DEFAULT_PIN are set in .env file:
python health_checker.py                    # Quick test using .env credentials
python health_checker.py -v --show-token   # Detailed test using .env credentials
```

## Integration

The health checker can be integrated into:

- **CI/CD pipelines** for automated testing
- **Monitoring systems** using exit codes
- **Student onboarding** for token generation
- **Classroom demonstrations** of API connectivity
