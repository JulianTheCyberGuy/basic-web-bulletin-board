<h1>Basic Web Bulletin Board</h1>

<p>
This project is a simple web-based bulletin board built with 
<strong>Flask (Python)</strong> and <strong>SQLite</strong>. 
Users can submit a post using their email address and a message, 
and all posts are displayed on the main page. 
The frontend uses HTML, CSS, and JavaScript, 
and communicates with the backend through a JSON API.
</p>

<p>
The page automatically checks for new posts every few seconds 
and updates without requiring a refresh.
</p>

<hr>

<h2>What This Project Demonstrates</h2>

<ul>
  <li>Flask routing</li>
  <li>REST-style API design</li>
  <li>SQLite database integration</li>
  <li>JSON request and response handling</li>
  <li>Client-side JavaScript fetch API</li>
  <li>Polling for updates</li>
  <li>Server-side input validation</li>
  <li>Basic web security practices</li>
</ul>

<hr>

<h2>Project Structure</h2>

<pre>
basic-web-bulletin-board/
│
├── app.py
├── schema.sql
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    └── main.js
</pre>

<hr>

<h2>File Descriptions</h2>

<p><strong>app.py</strong><br>
Main Flask application.<br>
- Serves the main page<br>
- Handles API routes<br>
- Validates input<br>
- Connects to SQLite<br>
- Initializes the database on startup
</p>

<p><strong>schema.sql</strong><br>
Defines the database schema.<br>
- Creates the <code>posts</code> table<br>
- Adds an index on <code>created_at</code>
</p>

<p><strong>templates/index.html</strong><br>
Main page layout.<br>
- Post submission form<br>
- Post display container<br>
- Loads <code>main.js</code>
</p>

<p><strong>static/main.js</strong><br>
Client-side logic.<br>
- Fetches posts from the API<br>
- Submits new posts<br>
- Polls the server every 5 seconds<br>
- Renders posts safely using <code>textContent</code>
</p>

<p><strong>requirements.txt</strong><br>
Lists required Python dependencies (Flask).
</p>

<hr>

<h2>Setup Instructions</h2>

<h3>1. Clone the Repository</h3>

<pre>
git clone https://github.com/JulianTheCyberGuy/basic-web-bulletin-board.git
cd basic-web-bulletin-board
</pre>

<h3>2. (Optional) Create a Virtual Environment</h3>

<p><strong>Mac/Linux:</strong></p>

<pre>
python3 -m venv .venv
source .venv/bin/activate
</pre>

<p><strong>Windows:</strong></p>

<pre>
python -m venv .venv
.venv\Scripts\activate
</pre>

<h3>3. Install Dependencies</h3>

<pre>
pip install -r requirements.txt
</pre>

<h3>4. Run the Application</h3>

<pre>
python app.py
</pre>

<p>
Open your browser and navigate to:<br>
<strong>http://127.0.0.1:5000</strong>
</p>

<hr>

<h2>API Endpoints</h2>

<p><strong>GET /api/posts</strong><br>
Returns all posts in JSON format.
</p>

<p><strong>GET /api/posts?since=&lt;timestamp&gt;</strong><br>
Returns only posts created after the provided timestamp.
</p>

<p><strong>POST /api/posts</strong><br>
Creates a new post.
</p>

<p>Example JSON body:</p>

<pre>
{
  "author_email": "name@example.com",
  "body": "Hello world!"
}
</pre>

<hr>

<h2>Validation Rules</h2>

<ul>
  <li>Email must contain "@" and a "." in the domain</li>
  <li>Email maximum length: 254 characters</li>
  <li>Body cannot be empty</li>
  <li>Body maximum length: 2000 characters</li>
</ul>

<p>
If validation fails, the server returns an error response.
</p>

<hr>

<h2>Security Notes</h2>

<ul>
  <li>Posts are rendered using <code>textContent</code> to prevent HTML injection.</li>
  <li>Input validation is enforced server-side.</li>
  <li>No authentication system (educational demo project).</li>
  <li>Uses Flask development server (not production ready).</li>
</ul>

<hr>

<h2>Limitations</h2>

<ul>
  <li>Uses polling instead of WebSockets (updates may be delayed up to 5 seconds).</li>
  <li>SQLite is for local development only.</li>
  <li>No login, moderation, or user management features.</li>
</ul>

<hr>

<p>
This project is intended for educational purposes and demonstrates foundational full-stack web development concepts.
</p>
