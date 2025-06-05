# BoulderBot

A Python-based web scraper for collecting boulder problem data from Mountain Project. This tool helps build a comprehensive database of boulder problems for analysis and reference.

## Features

- Ethical web scraping with proper delays and headers
- Detailed boulder problem information including:
  - Name and grade
  - Description
  - Location
  - URL reference
- SQLite database storage
- Rate limiting and retry mechanisms

## Setup

1. Clone the repository:
```bash
git clone https://github.com/ry-zeng/boulderbot.git
cd boulderbot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:
```bash
python populate_db.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.