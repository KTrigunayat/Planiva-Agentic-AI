# Planiva: Hybrid Web Scraper for Wedding Venues

A powerful Python-based web scraper that combines Selenium and BeautifulSoup for efficient data extraction from wedding planning websites. This hybrid approach provides both the reliability of browser automation and the speed of HTML parsing.

## ✨ Features

- **Hybrid Scraping**: Combines Selenium WebDriver and BeautifulSoup for optimal performance and reliability
- **Intelligent Data Extraction**: Extracts comprehensive venue details including:
  - Basic information (name, location, address)
  - Pricing and ratings (with smart price conversion)
  - Capacity details (seating, floating, indoor/outdoor)
  - Venue policies (catering, decor, alcohol, music, timing, parking)
  - Contact information (phone, email, website)
  - Image gallery and media
- **Advanced Features**:
  - Automatic ChromeDriver management
  - Headless browsing support
  - Debug mode with HTML snapshots
  - Robust error handling and logging
  - Type hints for better code maintainability
  - Environment variable support for configuration

## 🛠️ Prerequisites

- Python 3.7+
- Google Chrome browser installed
- ChromeDriver (automatically managed by `webdriver-manager`)

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Planiva-AgenticAI.git
   cd Planiva-AgenticAI
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   The main dependencies include:
   - beautifulsoup4: For HTML parsing
   - pandas: For data manipulation
   - transformers: For potential NLP tasks
   - torch: Required for transformers
   - selenium: For browser automation
   - webdriver-manager: For automatic ChromeDriver management

## 🏃‍♂️ Usage

### Basic Usage

Run the scraper with a target URL:
```bash
python Complete.py "https://www.wedmegood.com/wedding-venues/venue-name-12345"
```

### Command-line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `url` | URL of the venue page to scrape | Required |
| `--output`, `-o` | Save results to a JSON file | None |
| `--debug` | Enable debug mode (saves HTML snapshots) | False |

Example with all options:
```bash
python Complete.py "https://www.wedmegood.com/venue-example" --output venue_data.json --debug
```

### Environment Variables

Create a `.env` file to configure the scraper:
```env
DEBUG=true
HEADLESS=true
TIMEOUT=30
```

## 📊 Output Format

The scraper returns a structured JSON object with the following format:

```json
{
  "name": "Grand Ballroom Venue",
  "location": "Mumbai, Maharashtra",
  "address": "123 Wedding Street, Mumbai - 400001",
  "price": {
    "starting": "₹1,50,000",
    "subtitle": "Starting price per event",
    "numeric_value": 150000,
    "currency": "INR"
  },
  "rating": 4.7,
  "reviews_count": 128,
  "description": "Elegant venue with modern amenities...",
  "capacity": [
    {
      "area": "Main Hall",
      "type": "Indoor",
      "seating": 200,
      "floating": 250,
      "dimensions": "60x40 ft"
    },
    {
      "area": "Garden",
      "type": "Outdoor",
      "seating": 150,
      "floating": 200,
      "dimensions": "80x60 ft"
    }
  ],
  "amenities": [
    "AC",
    "Parking",
    "Dance Floor",
    "Stage",
    "Bridal Room"
  ],
  "policies": {
    "catering": "In-house catering available or external allowed with fee",
    "decor": "External decorators allowed with prior approval",
    "alcohol": "Allowed, no outside alcohol",
    "music": "Allowed until 10 PM, DJ/live music permitted",
    "timing": "6:00 AM to 11:00 PM",
    "parking": "Valet parking available for 50 cars"
  },
  "contact": {
    "phone": "+911234567890",
    "email": "venue@example.com",
    "website": "https://venuewebsite.com"
  },
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "source_url": "https://www.wedmegood.com/wedding-venues/venue-name",
  "scraped_at": "2023-01-01 12:00:00"
}
```

## Debugging

When run with the `--debug` flag, the scraper saves additional files in a `debug` directory:

- `rendered_page.html`: The final rendered HTML of the page
- `extracted_data.json`: Raw JSON data extracted from the page
- `js_extracted_data.json`: Data extracted using JavaScript execution
- `*.log`: Error and processing logs

## Customization

To modify the scraper for different websites or to extract additional data:

1. Update the `_process_venue_data` method to handle different data structures
2. Modify the XPath/CSS selectors in `_extract_json_from_page` if the page structure changes
3. Add new methods to extract additional information as needed

## Limitations

- The scraper is specifically designed for WedMeGood's website structure
- May require updates if the target website changes its structure
- Rate limiting or IP blocking may occur with excessive requests

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

*Note: This tool is for educational purposes only. Please respect the target website's terms of service and robots.txt file when scraping.*
