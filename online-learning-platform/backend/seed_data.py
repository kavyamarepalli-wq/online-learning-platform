"""Starter course content used by seed.py and tools/make_seed_assets.py."""


def lesson(slug, title, points, notes):
    return {"slug": slug, "title": title, "points": points, "notes": notes.strip()}


def q(prompt, options, correct, explanation):
    return {"prompt": prompt, "options": options, "correct": correct, "explanation": explanation}


INSTRUCTORS = [
    {"name": "Priya Sharma", "email": "priya@learnsphere.example",
     "headline": "Full Stack Developer and Mentor", "expertise": "HTML, CSS, JavaScript, Python",
     "bio": "Builds web applications and enjoys helping beginners write their first projects."},
    {"name": "Arjun Mehta", "email": "arjun@learnsphere.example",
     "headline": "Database and Cloud Engineer", "expertise": "SQL, Cloud, UI design",
     "bio": "Works with data and cloud systems and teaches them with practical examples."},
]

STUDENTS = [
    {"name": "Ananya Rao", "email": "ananya@learnsphere.example"},
    {"name": "Rahul Verma", "email": "rahul@learnsphere.example"},
]

COURSES = [
    {
        "slug": "html-css", "title": "HTML and CSS Foundations", "category": "Web Development",
        "level": "Beginner", "instructor": 0, "featured": False,
        "summary": "Build clean, responsive web pages from scratch with semantic HTML and modern CSS.",
        "description": "Start with the structure of a web page, then style it and make it work on any "
                       "screen size. By the end you can build a responsive page on your own.",
        "lessons": [
            lesson("page-structure", "The structure of a web page",
                   ["HTML describes content", "Use semantic elements", "head holds page settings"],
                   """
HTML describes the content of a page using elements. A document starts with <!doctype html>,
followed by the html, head and body elements.

Prefer semantic elements such as header, nav, main, article and footer. They tell browsers and
screen readers what each part of the page means.

Practice: create a page with a heading, a paragraph, a list and a link."""),
            lesson("box-model", "Styling and the box model",
                   ["Content, padding, border, margin", "Use box-sizing: border-box",
                    "Classes make styles reusable"],
                   """
Every element is a box made of content, padding, border and margin. Setting
box-sizing: border-box makes width include padding and border, which is easier to reason about.

Use classes to reuse styles. When rules conflict, specificity and then source order decide.

Practice: style a card with padding, a border radius and a soft shadow."""),
            lesson("responsive", "Responsive layouts",
                   ["Flexbox for one direction", "Grid for two directions",
                    "Media queries adapt layouts"],
                   """
Flexbox arranges items along one axis. CSS Grid arranges rows and columns together.

A media query applies styles at certain screen widths. Add the viewport meta tag so phones use
their real width.

Practice: turn a three column card grid into one column on small screens."""),
        ],
        "quiz": [
            q("Which element is the best choice for the main navigation links?",
              ["<div>", "<nav>", "<span>", "<section>"], 1,
              "nav is the semantic element for navigation."),
            q("What does box-sizing: border-box change?",
              ["Width includes padding and border", "Margins disappear",
               "Borders become square", "Content is hidden"], 0,
              "The declared width then covers content, padding and border."),
            q("Which tool is designed for rows and columns together?",
              ["float", "Flexbox", "CSS Grid", "position: absolute"], 2,
              "Grid is two-dimensional."),
            q("What applies CSS only at certain screen widths?",
              ["A pseudo-class", "A media query", "An id selector", "A comment"], 1,
              "Media queries test features such as viewport width."),
        ],
    },
    {
        "slug": "javascript", "title": "JavaScript Essentials", "category": "Web Development",
        "level": "Beginner", "instructor": 0, "featured": True,
        "summary": "Learn variables, functions, the DOM and asynchronous code to make pages interactive.",
        "description": "A practical introduction to the language of the web, from values and "
                       "functions to events and fetching data from an API.",
        "lessons": [
            lesson("values", "Variables and data types",
                   ["Use const by default", "Use let when values change", "Compare with ==="],
                   """
Declare variables with const, or let when the value must change. Common types are string, number,
boolean, null, undefined and object.

Use === to compare without type conversion.

Practice: store your name and age and print a sentence with a template string."""),
            lesson("functions", "Functions and arrays",
                   ["Functions group reusable logic", "map transforms arrays",
                    "filter selects items"],
                   """
A function takes inputs and returns a result. Arrow functions are a short form.

Arrays have useful methods: map returns a transformed copy, filter keeps matching items and
reduce combines items into one value.

Practice: from a list of marks, keep those above 40 and double them."""),
            lesson("dom-async", "Events, the DOM and fetch",
                   ["Select elements to update them", "Listen for events",
                    "await waits for a promise"],
                   """
The DOM represents the page as objects. Select an element with querySelector and react to user
actions with addEventListener.

fetch returns a promise. Inside an async function, await pauses until the result is ready. Always
check response.ok and handle errors.

Practice: add a button that loads data and shows it in a list."""),
        ],
        "quiz": [
            q("Which keyword declares a variable that cannot be reassigned?",
              ["var", "let", "const", "static"], 2, "const bindings cannot be reassigned."),
            q("What does [1, 2, 3].map(x => x * 2) return?",
              ["[2, 4, 6]", "[1, 2, 3]", "12", "undefined"], 0,
              "map builds a new array from the results."),
            q("What does the === operator compare?",
              ["Value only", "Type only", "Value and type", "Memory size"], 2,
              "Strict equality does not convert types."),
            q("What does fetch() return?",
              ["A string", "A promise", "An array", "A DOM node"], 1,
              "fetch resolves to a Response through a promise."),
        ],
    },
    {
        "slug": "python", "title": "Python Programming for Beginners", "category": "Programming",
        "level": "Beginner", "instructor": 0, "featured": True,
        "summary": "Write readable Python programs using variables, loops, functions and collections.",
        "description": "No experience needed. Learn the core building blocks of Python through "
                       "short lessons and practice tasks.",
        "lessons": [
            lesson("basics", "First steps in Python",
                   ["print shows output", "input reads text", "Indentation matters"],
                   """
Python code reads almost like English. print() writes output and input() reads a line of text,
which you can convert with int() or float().

Blocks are defined by indentation, usually four spaces.

Practice: ask for two numbers and print their sum."""),
            lesson("loops", "Conditions and loops",
                   ["if, elif, else choose a path", "for repeats over items",
                    "while repeats on a condition"],
                   """
Use if, elif and else to make decisions. A for loop visits each item of a sequence, and range()
produces numbers. A while loop continues as long as its condition is true.

Practice: print the multiplication table of any number."""),
            lesson("collections", "Functions and collections",
                   ["def creates a function", "Lists keep order", "Dictionaries map keys"],
                   """
Define functions with def and return results. Lists are ordered and changeable, tuples are ordered
and fixed, sets hold unique items and dictionaries map keys to values.

Practice: count how often each word appears in a sentence."""),
        ],
        "quiz": [
            q("Which of these creates a dictionary?", ["[1, 2]", "(1, 2)", "{'a': 1}", "{1, 2}"], 2,
              "Key and value pairs in braces make a dictionary."),
            q("What does range(3) produce?", ["1, 2, 3", "0, 1, 2", "0, 1, 2, 3", "3"], 1,
              "range starts at 0 and stops before the end value."),
            q("How are code blocks defined in Python?",
              ["Braces", "Semicolons", "Indentation", "The end keyword"], 2,
              "Indentation groups statements."),
            q("Which keyword defines a function?", ["func", "def", "function", "lambda only"], 1,
              "def starts a function definition."),
        ],
    },
    {
        "slug": "sql", "title": "SQL and Database Design", "category": "Databases",
        "level": "Intermediate", "instructor": 1, "featured": True,
        "summary": "Model data with tables and keys, then query it confidently with SQL.",
        "description": "Understand relational design, write queries with joins and aggregates, and "
                       "keep your data consistent.",
        "lessons": [
            lesson("tables", "Tables and keys",
                   ["Rows are records", "Primary keys identify rows", "Foreign keys link tables"],
                   """
A relational database stores data in tables. Each row is a record and each column an attribute.

A primary key uniquely identifies a row. A foreign key refers to a key in another table and keeps
references valid.

Practice: design tables for students, courses and enrollments."""),
            lesson("queries", "Selecting and joining",
                   ["SELECT chooses columns", "WHERE filters rows", "JOIN combines tables"],
                   """
SELECT chooses columns and WHERE filters rows. An INNER JOIN keeps matching rows from both tables,
while a LEFT JOIN keeps every row from the left table.

Practice: list each student with the titles of their courses."""),
            lesson("normalisation", "Grouping and normalisation",
                   ["GROUP BY summarises rows", "Avoid repeated data", "Index frequent searches"],
                   """
Aggregate functions such as COUNT and AVG summarise groups created by GROUP BY. HAVING filters
those groups.

Normalisation removes repeated data so each fact is stored once. Indexes speed up searches at the
cost of extra storage and slower writes.

Practice: count enrollments for every course."""),
        ],
        "quiz": [
            q("What does a primary key do?",
              ["Sorts a table", "Uniquely identifies each row", "Encrypts data",
               "Links two databases"], 1, "No two rows share a primary key."),
            q("Which join keeps all rows from the left table?",
              ["INNER JOIN", "CROSS JOIN", "LEFT JOIN", "SELF JOIN"], 2,
              "Unmatched right-side columns become NULL."),
            q("Which clause filters groups after aggregation?",
              ["WHERE", "HAVING", "ORDER BY", "LIMIT"], 1, "HAVING applies to groups."),
            q("What is the main goal of normalisation?",
              ["Reduce repeated data", "Make files larger", "Remove all keys",
               "Avoid using SQL"], 0, "Each fact should be stored once."),
        ],
    },
    {
        "slug": "ui-design", "title": "UI and UX Design Principles", "category": "Design",
        "level": "Beginner", "instructor": 1, "featured": False,
        "summary": "Design interfaces people understand using hierarchy, contrast and user testing.",
        "description": "Learn the principles behind usable interfaces and apply them to your own "
                       "screens.",
        "lessons": [
            lesson("users", "Understanding users",
                   ["Start from user goals", "Ask open questions", "Sketch the main tasks"],
                   """
Good design starts with what people are trying to achieve. Interview a few users, listen for their
goals and problems, and list the main tasks.

Practice: write three tasks a student performs on a learning website."""),
            lesson("hierarchy", "Visual hierarchy",
                   ["Size shows importance", "Group related items", "Keep spacing consistent"],
                   """
Size, weight, colour and spacing guide the eye. Place related items close together and use a
consistent spacing scale.

Ensure text has enough contrast with its background.

Practice: redesign a cluttered form with clear groups."""),
            lesson("testing", "Testing your design",
                   ["Watch people use it", "Fix the biggest problem first", "Test again"],
                   """
Usability testing means watching real people try tasks. Do not explain the interface; note where
they hesitate. Fix the most serious problem and test again.

Practice: ask a friend to complete a task and record where they struggle."""),
        ],
        "quiz": [
            q("What should a design process start from?",
              ["Favourite colours", "User goals", "Animations", "The logo"], 1,
              "Understanding goals guides later decisions."),
            q("How do you show that items belong together?",
              ["Place them close together", "Use random colours", "Hide them",
               "Make them blink"], 0, "Proximity signals a relationship."),
            q("During a usability test you should mainly...",
              ["Explain every button", "Observe where people struggle", "Sell the product",
               "Complete tasks for them"], 1, "Observation reveals real problems."),
            q("Why does contrast matter?",
              ["It makes pages load faster", "It keeps text readable", "It saves storage",
               "It removes bugs"], 1, "Low contrast text is hard to read."),
        ],
    },
    {
        "slug": "cloud", "title": "Cloud Computing Fundamentals", "category": "Cloud Computing",
        "level": "Intermediate", "instructor": 1, "featured": False,
        "summary": "Understand cloud service models and deploy applications safely.",
        "description": "Explore compute, storage and databases in the cloud, and learn how to "
                       "configure applications with environment variables.",
        "lessons": [
            lesson("models", "Cloud service models",
                   ["IaaS rents infrastructure", "PaaS runs your code", "SaaS is ready to use"],
                   """
Infrastructure as a Service provides virtual machines and networks. Platform as a Service runs your
code without server management. Software as a Service delivers complete applications.

Practice: name one example of each model you have used."""),
            lesson("storage", "Compute, storage and databases",
                   ["Keep servers stateless", "Object storage holds files",
                    "Managed databases handle upkeep"],
                   """
Application servers should be stateless so they can be restarted or scaled. Files belong in object
storage and structured data in a database.

Practice: draw where a learning platform keeps videos, accounts and code."""),
            lesson("secrets", "Configuration and security",
                   ["Secrets go in environment variables", "Never commit passwords",
                    "Always use HTTPS"],
                   """
Store configuration such as database addresses and secret keys in environment variables, never in
source code. Give each service only the access it needs and serve traffic over HTTPS.

Practice: list the environment variables your next project needs."""),
        ],
        "quiz": [
            q("Which model runs your code without managing servers?",
              ["IaaS", "PaaS", "SaaS", "None"], 1, "The platform manages the servers."),
            q("Where should uploaded videos usually be stored?",
              ["In object storage", "In source code", "In browser cookies",
               "In an environment variable"], 0, "Object storage is made for files."),
            q("Where should a database password be kept?",
              ["In the Git repository", "In frontend JavaScript", "In an environment variable",
               "In a public README"], 2, "Secrets stay out of code."),
            q("Why keep application servers stateless?",
              ["To make them easier to restart and scale", "To avoid using a network",
               "To delete the database", "To disable HTTPS"], 0,
              "Any instance can then serve any request."),
        ],
    },
]
