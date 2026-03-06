</head>

<body>

<h1>Basic Web Bulletin Board</h1>

<p>
A simple Flask-based bulletin board demonstrating <b>secure session handling, user authentication, and posting functionality</b>. 
Users can register, log in, and create posts associated with their authenticated session.
</p>

<p>
This project was originally developed as part of a <b>session management exercise</b> and later expanded with additional usability improvements and deployment support.
</p>


<div class="section">
<h2>Features</h2>

<h3>Authentication and Session Handling</h3>
<ul>
<li>User registration with email and password</li>
<li>Secure password hashing using Werkzeug</li>
<li>Cryptographically secure session IDs</li>
<li>Cookie-based authentication</li>
<li>Session validation on every request</li>
<li>Posts restricted to authenticated users</li>
<li>Author email automatically attached to posts via session lookup</li>
</ul>

<h3>Bulletin Board Functionality</h3>
<ul>
<li>Create posts while logged in</li>
<li>Posts show the email of the authenticated user</li>
<li>Posts stored in a SQLite database</li>
<li>Posts displayed in a clean feed layout</li>
<li>Character counter for post length</li>
<li>Refresh button to reload posts</li>
</ul>

<h3>User Experience Improvements</h3>
<ul>
<li>Modernized interface</li>
<li>Registration and login panels</li>
<li>Success and error messaging</li>
<li>Login highlighting after registration</li>
<li>Auto-filled login email after registration</li>
<li>Empty state when no posts exist</li>
<li>Avatar initials generated from user email</li>
<li>Form loading indicators</li>
<li>Post timestamps formatted for readability</li>
</ul>

<h3>Security Features</h3>
<ul>
<li>Cryptographically random session IDs</li>
<li>Cookie-based session storage</li>
<li>Password hashing</li>
<li>HTML escaping to prevent XSS</li>
<li>Input validation for forms</li>
<li>Server-side session verification before posting</li>
</ul>

<h3>Deployment Improvements</h3>
<ul>
<li>SQLite schema initialization on startup</li>
<li>Database migration protection</li>
<li>Gunicorn production server</li>
<li>Render deployment support</li>
<li>Environment-based port configuration</li>
</ul>
</div>


<div class="section">
<h2>Database Schema</h2>

<h3>Users Table</h3>
<table>
<tr>
<th>Column</th>
<th>Description</th>
</tr>
<tr>
<td>user_id</td>
<td>Unique user identifier</td>
</tr>
<tr>
<td>email</td>
<td>User email address</td>
</tr>
<tr>
<td>password_hash</td>
<td>Securely hashed password</td>
</tr>
</table>


<h3>Sessions Table</h3>
<table>
<tr>
<th>Column</th>
<th>Description</th>
</tr>
<tr>
<td>session_id</td>
<td>Cryptographically generated session identifier</td>
</tr>
<tr>
<td>user_id</td>
<td>Associated user</td>
</tr>
<tr>
<td>expires_at</td>
<td>Session expiration timestamp</td>
</tr>
</table>


<h3>Posts Table</h3>
<table>
<tr>
<th>Column</th>
<th>Description</th>
</tr>
<tr>
<td>id</td>
<td>Post ID</td>
</tr>
<tr>
<td>author_email</td>
<td>Email of the user who created the post</td>
</tr>
<tr>
<td>body</td>
<td>Post content</td>
</tr>
<tr>
<td>created_at</td>
<td>Timestamp</td>
</tr>
</table>

</div>


<div class="section">
<h2>How Session Handling Works</h2>

<ol>
<li>User registers and password is hashed before storage.</li>
<li>User logs in and server generates a <b>cryptographically random session ID</b>.</li>
<li>The session ID is stored in the <b>sessions table</b>.</li>
<li>The session ID is sent to the browser as a <b>cookie</b>.</li>
<li>Every request checks the cookie for a valid session.</li>
<li>If valid, the server retrieves the user linked to the session.</li>
<li>The authenticated user can create posts.</li>
</ol>

<p>If a session is invalid or missing, the user cannot create posts.</p>

</div>


<div class="section">
<h2>Project Structure</h2>

<pre>
basic-web-bulletin-board
│
├── app.py
├── schema.sql
├── requirements.txt
├── render.yaml
│
├── templates
│   └── index.html
│
├── static
│   └── styles.css  
│   └── main.js
│
└── README.md
</pre>

</div>


<div class="section">
<h2>Running Locally</h2>

<h3>Install dependencies</h3>

<pre>
pip install -r requirements.txt
</pre>

<h3>Start the server</h3>

<pre>
python app.py
</pre>

<p>The application will run at:</p>

<code>http://localhost:5000</code>

</div>


<div class="section">
<h2>Production Deployment</h2>

<p>This project is configured for deployment on <b>Render</b> using Gunicorn.</p>

<pre>
gunicorn app:app --bind 0.0.0.0:$PORT
</pre>

<p>The database schema initializes automatically on startup.</p>

</div>


<div class="section">
<h2>Technologies Used</h2>

<ul>
<li>Python</li>
<li>Flask</li>
<li>SQLite</li>
<li>Gunicorn</li>
<li>HTML</li>
<li>CSS</li>
<li>JavaScript</li>
<li>Render (deployment)</li>
</ul>

</div>


<div class="section">
<h2>Assignment Requirements Covered</h2>

<ul>
<li>Users table implemented</li>
<li>Sessions table implemented</li>
<li>Cryptographically generated session IDs</li>
<li>Cookie-based session authentication</li>
<li>Posts require a valid session</li>
<li>Post author email pulled via session → user lookup</li>
</ul>

</div>


<div class="section">
<h2>Additional Enhancements</h2>

<ul>
<li>Improved user interface</li>
<li>Deployment configuration</li>
<li>Session expiration support</li>
<li>Better user feedback and messaging</li>
<li>Modern frontend layout</li>
<li>Production-style error handling</li>
</ul>

</div>


<div class="section">
<h2>Demonstration</h2>

<p>The demonstration video shows:</p>

<ul>
<li>User registration</li>
<li>Login and session creation</li>
<li>Cookie-based authentication</li>
<li>Authenticated post creation</li>
<li>Session-based author identification</li>
</ul>

</div>


<div class="section">
<h2>License</h2>

<p>This project was created for educational purposes.</p>
</div>


</body>
</html>