#!/usr/bin/env python3
"""
Interactive Flashcard Quiz for ML Exam Preparation
Web-based interface using Flask with KaTeX for LaTeX rendering.
"""

import re
import random
import json
from pathlib import Path
from typing import List, Tuple
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Global storage for flashcards
flashcard_data = {
    'cards': [],
    'current_index': 0,
    'score': 0,
    'answered': 0,
    'showing_answer': False
}


def parse_latex_file(filepath: str) -> List[Tuple[str, str]]:
    """Parse a LaTeX file and extract question-answer pairs."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    section_pattern = r'\\section\{([^}]+)\}'
    sections = list(re.finditer(section_pattern, content))
    
    flashcards = []
    for i, match in enumerate(sections):
        question = match.group(1).strip()
        answer_start = match.end()
        
        if i + 1 < len(sections):
            answer_end = sections[i + 1].start()
        else:
            next_part = re.search(r'\\part\{', content[answer_start:])
            if next_part:
                answer_end = answer_start + next_part.start()
            else:
                answer_end = len(content)
        
        answer = content[answer_start:answer_end].strip()
        
        if question and answer:
            flashcards.append((question, answer))
    
    return flashcards


def load_all_flashcards(lectures_dir: str) -> List[Tuple[str, str, str]]:
    """Load flashcards from all lecture files."""
    all_cards = []
    lectures_path = Path(lectures_dir)
    
    for tex_file in sorted(lectures_path.glob('lecture_*.tex')):
        cards = parse_latex_file(str(tex_file))
        for question, answer in cards:
            all_cards.append((question, answer, tex_file.name))
    
    return all_cards


def prepare_latex_for_katex(text: str) -> str:
    """Convert LaTeX text for KaTeX rendering in HTML."""
    # Convert display math \[...\] to $$...$$
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    
    # Handle environments
    text = re.sub(r'\\begin\{algorithm\}', '<div class="algorithm">', text)
    text = re.sub(r'\\end\{algorithm\}', '</div>', text)
    text = re.sub(r'\\begin\{algorithmic\}\[\d*\]', '<div class="algorithmic">', text)
    text = re.sub(r'\\end\{algorithmic\}', '</div>', text)
    
    # Convert text formatting to HTML
    text = re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', text)
    text = re.sub(r'\\textit\{([^}]+)\}', r'<em>\1</em>', text)
    text = re.sub(r'\\emph\{([^}]+)\}', r'<em>\1</em>', text)
    
    # Handle itemize/enumerate - convert to HTML lists
    text = re.sub(r'\\begin\{itemize\}', '<ul>', text)
    text = re.sub(r'\\end\{itemize\}', '</ul>', text)
    text = re.sub(r'\\begin\{enumerate\}', '<ol>', text)
    text = re.sub(r'\\end\{enumerate\}', '</ol>', text)
    text = re.sub(r'\\item\[(.*?)\]', r'<li><strong>\1</strong> ', text)
    text = re.sub(r'\\item', '<li>', text)
    
    # Handle subsections
    text = re.sub(r'\\subsection\*?\{([^}]+)\}', r'<h4>\1</h4>', text)
    
    # Algorithm commands
    text = re.sub(r'\\Require', '<span class="algo-keyword">Require:</span>', text)
    text = re.sub(r'\\Ensure', '<span class="algo-keyword">Ensure:</span>', text)
    text = re.sub(r'\\State', '<br>&nbsp;&nbsp;', text)
    text = re.sub(r'\\Repeat', '<span class="algo-keyword">Repeat:</span>', text)
    text = re.sub(r'\\Until', '<span class="algo-keyword">Until:</span>', text)
    text = re.sub(r'\\If', '<span class="algo-keyword">If</span>', text)
    text = re.sub(r'\\Else', '<span class="algo-keyword">Else</span>', text)
    text = re.sub(r'\\EndIf', '', text)
    text = re.sub(r'\\For', '<span class="algo-keyword">For</span>', text)
    text = re.sub(r'\\EndFor', '', text)
    text = re.sub(r'\\Return', '<span class="algo-keyword">Return:</span>', text)
    
    # Spacing and line breaks
    text = re.sub(r'\\quad', '&emsp;', text)
    text = re.sub(r'\\qquad', '&emsp;&emsp;', text)
    text = re.sub(r'\\;', '&thinsp;', text)
    text = re.sub(r'\\,', '&thinsp;', text)
    text = re.sub(r'\\!', '', text)
    text = re.sub(r'\\\\', '<br>', text)
    text = re.sub(r'\\newline', '<br>', text)
    
    # Convert newlines to <br> for display (but not inside math)
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            result.append(stripped)
        else:
            result.append('<br>')
    text = '\n'.join(result)
    
    return text


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ML Exam Flashcards</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    <style>
        :root {
            --bg-primary: #1e1e1e;
            --bg-secondary: #252526;
            --bg-tertiary: #2d2d2d;
            --text-primary: #d4d4d4;
            --text-secondary: #9cdcfe;
            --accent-blue: #569cd6;
            --accent-green: #4ec9b0;
            --accent-orange: #ce9178;
            --accent-yellow: #dcdcaa;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: var(--bg-secondary);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .progress {
            font-size: 1.2em;
            color: var(--accent-blue);
            font-weight: bold;
        }
        
        .score {
            color: var(--accent-green);
            font-size: 1.1em;
        }
        
        .source {
            color: var(--text-secondary);
            font-size: 0.9em;
        }
        
        .card {
            background: var(--bg-secondary);
            border-radius: 10px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        
        .card-header {
            padding: 15px 20px;
            font-weight: bold;
            font-size: 1.1em;
            border-bottom: 2px solid;
        }
        
        .card-header.question {
            color: var(--accent-blue);
            border-color: var(--accent-blue);
        }
        
        .card-header.answer {
            color: var(--accent-green);
            border-color: var(--accent-green);
        }
        
        .card-content {
            padding: 20px;
            line-height: 1.7;
            font-size: 1.05em;
        }
        
        .card-content h4 {
            color: var(--accent-yellow);
            margin: 20px 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 1px solid var(--bg-tertiary);
        }
        
        .card-content ul, .card-content ol {
            margin: 10px 0 10px 25px;
        }
        
        .card-content li {
            margin: 8px 0;
        }
        
        .card-content strong {
            color: var(--accent-orange);
        }
        
        .card-content em {
            color: var(--text-secondary);
        }
        
        .algorithm {
            background: var(--bg-tertiary);
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            font-family: 'Consolas', monospace;
        }
        
        .algo-keyword {
            color: var(--accent-blue);
            font-weight: bold;
        }
        
        .hidden-answer {
            text-align: center;
            padding: 40px;
            color: #6a9955;
            font-style: italic;
            font-size: 1.1em;
        }
        
        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            padding: 20px;
            background: var(--bg-secondary);
            border-radius: 10px;
        }
        
        button {
            padding: 12px 20px;
            font-size: 1em;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .btn-nav {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        
        .btn-show {
            background: var(--accent-blue);
            color: white;
            min-width: 180px;
        }
        
        .btn-wrong {
            background: #c94040;
            color: white;
        }
        
        .btn-partial {
            background: #c9a040;
            color: white;
        }
        
        .btn-correct {
            background: #40c970;
            color: white;
        }
        
        .btn-shuffle {
            background: var(--accent-orange);
            color: white;
        }
        
        .rating-section {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .rating-label {
            color: #808080;
            margin-right: 5px;
        }
        
        .katex-display {
            margin: 15px 0;
            overflow-x: auto;
            overflow-y: hidden;
        }
        
        .katex {
            color: var(--accent-orange);
        }
        
        /* Lecture selector */
        .lecture-selector {
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 10px;
            max-width: 500px;
            margin: 50px auto;
        }
        
        .lecture-selector h2 {
            color: var(--accent-blue);
            margin-bottom: 20px;
            text-align: center;
        }
        
        .lecture-option {
            display: flex;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: var(--bg-tertiary);
            border-radius: 5px;
            cursor: pointer;
        }
        
        .lecture-option:hover {
            background: #3d3d3d;
        }
        
        .lecture-option input {
            margin-right: 15px;
            width: 18px;
            height: 18px;
        }
        
        .lecture-option label {
            cursor: pointer;
            flex: 1;
        }
        
        .selector-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            justify-content: center;
        }
        
        kbd {
            background: var(--bg-tertiary);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-left: 5px;
        }
        
        @media (max-width: 600px) {
            .controls {
                flex-direction: column;
            }
            button {
                width: 100%;
            }
            header {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="selector" style="display: none;">
            <div class="lecture-selector">
                <h2>📚 Select Lectures</h2>
                <div id="lecture-options"></div>
                <div class="selector-buttons">
                    <button class="btn-nav" onclick="selectAll(true)">Select All</button>
                    <button class="btn-nav" onclick="selectAll(false)">Select None</button>
                    <button class="btn-show" onclick="startQuiz()">Start ▶</button>
                </div>
            </div>
        </div>
        
        <div id="quiz" style="display: none;">
            <header>
                <span class="progress" id="progress">Card 1 of 48</span>
                <span class="score" id="score">Score: 0/0</span>
                <span class="source" id="source">lecture_01.tex</span>
            </header>
            
            <div class="card">
                <div class="card-header question">❓ QUESTION</div>
                <div class="card-content" id="question-content"></div>
            </div>
            
            <div class="card">
                <div class="card-header answer">💡 ANSWER</div>
                <div class="card-content" id="answer-content">
                    <div class="hidden-answer">Press SPACE or click "Show Answer" to reveal</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn-nav" onclick="prevCard()">◀ Previous<kbd>←</kbd></button>
                <button class="btn-show" id="show-btn" onclick="toggleAnswer()">Show Answer<kbd>Space</kbd></button>
                <button class="btn-nav" onclick="nextCard()">Next ▶<kbd>→</kbd></button>
                
                <span class="rating-label">│ Rate:</span>
                <div class="rating-section">
                    <button class="btn-wrong" onclick="rate(0)">❌ Wrong<kbd>1</kbd></button>
                    <button class="btn-partial" onclick="rate(0.5)">◐ Partial<kbd>2</kbd></button>
                    <button class="btn-correct" onclick="rate(1)">✓ Correct<kbd>3</kbd></button>
                </div>
                
                <button class="btn-shuffle" onclick="shuffle()">🔀 Shuffle</button>
            </div>
        </div>
    </div>
    
    <script>
        let allCards = [];
        let cards = [];
        let currentIndex = 0;
        let showingAnswer = false;
        let score = 0;
        let answered = 0;
        
        // Load cards on page load
        fetch('/api/cards')
            .then(r => r.json())
            .then(data => {
                allCards = data.cards;
                showSelector();
            });
        
        function showSelector() {
            const sources = [...new Set(allCards.map(c => c.source))];
            const container = document.getElementById('lecture-options');
            container.innerHTML = sources.map(s => {
                const count = allCards.filter(c => c.source === s).length;
                return `
                    <div class="lecture-option">
                        <input type="checkbox" id="${s}" checked>
                        <label for="${s}">${s} (${count} questions)</label>
                    </div>
                `;
            }).join('');
            document.getElementById('selector').style.display = 'block';
        }
        
        function selectAll(value) {
            document.querySelectorAll('#lecture-options input').forEach(cb => cb.checked = value);
        }
        
        function startQuiz() {
            const selected = [];
            document.querySelectorAll('#lecture-options input:checked').forEach(cb => {
                selected.push(cb.id);
            });
            
            cards = allCards.filter(c => selected.includes(c.source));
            if (cards.length === 0) cards = allCards;
            
            currentIndex = 0;
            score = 0;
            answered = 0;
            showingAnswer = false;
            
            document.getElementById('selector').style.display = 'none';
            document.getElementById('quiz').style.display = 'block';
            displayCard();
        }
        
        function displayCard() {
            if (cards.length === 0) return;
            
            const card = cards[currentIndex];
            document.getElementById('progress').textContent = `Card ${currentIndex + 1} of ${cards.length}`;
            document.getElementById('score').textContent = `Score: ${score}/${answered}`;
            document.getElementById('source').textContent = card.source;
            document.getElementById('question-content').innerHTML = card.question;
            
            if (showingAnswer) {
                document.getElementById('answer-content').innerHTML = card.answer;
                document.getElementById('show-btn').textContent = 'Hide Answer';
            } else {
                document.getElementById('answer-content').innerHTML = 
                    '<div class="hidden-answer">Press SPACE or click "Show Answer" to reveal</div>';
                document.getElementById('show-btn').textContent = 'Show Answer';
            }
            
            // Render math
            renderMathInElement(document.getElementById('question-content'), {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false}
                ],
                throwOnError: false
            });
            
            if (showingAnswer) {
                renderMathInElement(document.getElementById('answer-content'), {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '$', right: '$', display: false}
                    ],
                    throwOnError: false
                });
            }
        }
        
        function toggleAnswer() {
            showingAnswer = !showingAnswer;
            displayCard();
        }
        
        function prevCard() {
            if (currentIndex > 0) {
                currentIndex--;
                showingAnswer = false;
                displayCard();
            }
        }
        
        function nextCard() {
            if (currentIndex < cards.length - 1) {
                currentIndex++;
                showingAnswer = false;
                displayCard();
            }
        }
        
        function rate(points) {
            if (!showingAnswer) {
                toggleAnswer();
                return;
            }
            score += points;
            answered++;
            nextCard();
        }
        
        function shuffle() {
            for (let i = cards.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [cards[i], cards[j]] = [cards[j], cards[i]];
            }
            currentIndex = 0;
            score = 0;
            answered = 0;
            showingAnswer = false;
            displayCard();
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT') return;
            
            switch(e.key) {
                case ' ':
                    e.preventDefault();
                    toggleAnswer();
                    break;
                case 'ArrowLeft':
                    prevCard();
                    break;
                case 'ArrowRight':
                    nextCard();
                    break;
                case '1':
                    rate(0);
                    break;
                case '2':
                    rate(0.5);
                    break;
                case '3':
                    rate(1);
                    break;
                case 'Escape':
                    document.getElementById('quiz').style.display = 'none';
                    document.getElementById('selector').style.display = 'block';
                    break;
            }
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/cards')
def get_cards():
    cards = []
    for question, answer, source in flashcard_data['cards']:
        cards.append({
            'question': prepare_latex_for_katex(question),
            'answer': prepare_latex_for_katex(answer),
            'source': source
        })
    return jsonify({'cards': cards})


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    lectures_dir = script_dir / 'lectures'
    
    if not lectures_dir.exists():
        print(f"Error: Lectures directory not found at {lectures_dir}")
        return
    
    print("Loading flashcards from LaTeX files...")
    flashcard_data['cards'] = load_all_flashcards(str(lectures_dir))
    
    if not flashcard_data['cards']:
        print("No flashcards found.")
        return
    
    num_cards = len(flashcard_data['cards'])
    num_lectures = len(set(c[2] for c in flashcard_data['cards']))
    print(f"✅ Loaded {num_cards} questions from {num_lectures} lecture files.")
    print("\n🌐 Starting web server...")
    print("   Open http://localhost:5000 in your browser")
    print("   Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
