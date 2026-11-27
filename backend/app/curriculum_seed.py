"""Seed original, introductory course lessons for local development."""
from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models.entities import Course, Lesson

COURSES = [
    {
        "title": "Python Fundamentals",
        "slug": "python-fundamentals",
        "category": "python",
        "difficulty": "beginner",
        "description": "Build a reliable Python foundation for placement coding rounds and technical interviews.",
        "lessons": [
            ("variables-and-types", "Variables, values and types", 18, """## Variables and values

A variable is a name bound to an object. Python infers the type from the object; you do not declare a type before assignment.

    name = "Ritik"
    attempts = 3
    accuracy = 0.85
    is_ready = False

Common built-in scalar types are int, float, bool, str and NoneType. Collections include list, tuple, set and dict.

## Conversion and inspection

Use int(), float(), str() and bool() to convert values when conversion is valid. Use type(value) to inspect a value and isinstance(value, SomeType) when checking a type in program logic.

Input from input() is always text. Convert it explicitly before arithmetic:

    age = int(input("Age: "))
    print(age + 1)

## Equality and identity

Use == to compare values. Use is mainly for identity checks such as value is None. Do not use is to compare ordinary strings or numbers.

## Practice

1. Read two integers and print their sum, difference and product.
2. Read a decimal number and print it rounded to two decimal places.
3. Read a value and report whether it is None, a boolean, a number or a string.
4. Predict the output of 7 // 2, 7 / 2 and 7 % 2.

**Common mistake:** input() returns str. Adding two input strings concatenates them; convert them to numbers when arithmetic is intended."""),
            ("conditions-and-loops", "Conditions, loops and digit problems", 22, """## Conditional execution

Use if, elif and else to choose a path. Conditions evaluate to truth values; comparisons include ==, !=, <, <=, > and >=. Combine conditions using and, or and not.

## Iteration

Use for when iterating over a sequence or range, and while when repetition depends on a condition.

    for number in range(1, 6):
        print(number)

    value = 9474
    total = 0
    while value > 0:
        digit = value % 10
        total += digit
        value //= 10

For a positive integer, n % 10 extracts the last digit and n // 10 removes it. Handle zero separately when counting digits; a loop conditioned on n > 0 executes zero times for input zero.

## Break and continue

break exits the nearest loop. continue skips to the next iteration. Avoid changing a loop counter in multiple places unless the logic is clear.

## Practice

1. Check whether a number is prime, handling values below 2.
2. Reverse an integer using remainder and integer division.
3. Count digits; return one digit for zero.
4. Check an Armstrong number using the number of digits.
5. Print a multiplication table.
6. Find the GCD of two positive integers with Euclid's algorithm.

**Debugging habit:** trace a small input by hand and write down the value of every variable after each iteration."""),
            ("collections", "Lists, tuples, sets and dictionaries", 24, """## Choose the right collection

- list: ordered, mutable sequence; supports indexing and slicing.
- tuple: ordered, immutable sequence; useful for fixed records.
- set: collection of unique hashable values; useful for membership and deduplication.
- dict: key-to-value mapping; useful for frequency counts and lookup.

    scores = [10, 20, 20]
    unique_scores = set(scores)
    frequency = {}
    for score in scores:
        frequency[score] = frequency.get(score, 0) + 1

## List operations

append adds one item, extend adds items from an iterable, pop removes and returns an item, and sort mutates the list. sorted returns a new sorted list. A slice such as nums[1:4] returns a new list containing the selected range.

## Complexity intuition

List indexing is O(1). Searching a list is O(n). Set membership and dictionary lookup are average O(1), assuming a healthy hash distribution. Sorting is typically O(n log n).

## Practice

1. Find the second-largest distinct value.
2. Count how many times each character appears.
3. Remove duplicates while preserving original order.
4. Group words by their first character.
5. Merge two dictionaries and explain how duplicate keys are resolved.

**Common mistake:** a set does not preserve a meaningful sorted order. Use sorted(my_set) when ordered output is required."""),
            ("functions-and-recursion", "Functions, scope and recursion", 22, """## Functions

A function groups reusable behaviour. Parameters are local names; return sends a value back to the caller.

    def is_even(number: int) -> bool:
        return number % 2 == 0

Prefer a return value over printing inside a function when another part of the program needs to use the result.

Default arguments are evaluated when the function is defined. Avoid mutable defaults such as an empty list; use None and create a fresh list inside the function.

## Scope

Python resolves names using local, enclosing, global and built-in scopes. A variable assigned inside a function is normally local unless declared global or nonlocal. Keep state local where practical.

## Recursion

A recursive function calls itself. Every recursive solution needs a base case and progress toward that base case.

    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)

Recursion can be elegant for trees and divide-and-conquer, but Python has a recursion limit. Iteration is often better for simple linear repetition.

## Practice

1. Write a function returning the minimum and maximum of a list.
2. Implement factorial iteratively and recursively.
3. Write a recursive sum of digits.
4. Explain why a recursive function without a reachable base case fails.
5. Rewrite a simple recursive Fibonacci solution using iteration."""),
            ("oop-and-exceptions", "OOP and exception handling", 25, """## Classes and objects

A class describes behaviour and state. An object is an instance of a class. __init__ initializes instance attributes; self refers to the current instance.

    class BankAccount:
        def __init__(self, owner, balance=0):
            self.owner = owner
            self.balance = balance

        def deposit(self, amount):
            if amount <= 0:
                raise ValueError("amount must be positive")
            self.balance += amount

## Encapsulation and inheritance

Encapsulation groups state and behaviour behind a well-defined interface. Python conventions use a leading underscore to mark non-public implementation details; this is a convention, not strict access control.

Inheritance lets a class reuse or specialize another class. Prefer composition when an object simply uses another object rather than being a subtype of it. Polymorphism means code can work with different objects through a shared interface.

## Exceptions

Use try/except for expected recoverable errors. Use finally for cleanup. Raise a specific exception when a function cannot fulfil its contract. Do not catch Exception broadly unless you can handle or report it meaningfully.

## Practice

1. Implement a Student class with a method that returns a grade.
2. Implement a BankAccount with deposit and withdraw validation.
3. Demonstrate inheritance with a base Employee and two specialized roles.
4. Read an integer and handle invalid text input.
5. Explain the difference between an instance attribute and a class attribute."""),
        ],
    },
    {
        "title": "SQL and DBMS",
        "slug": "sql-and-dbms",
        "category": "sql",
        "difficulty": "beginner",
        "description": "Learn relational query foundations through joins, grouping, CTEs and window functions.",
        "lessons": [
            ("select-and-filter", "SELECT, filtering and sorting", 18, """## Relational data

A table contains rows and columns. A primary key identifies a row; a foreign key references a key in another table. SQL describes the result you want rather than the exact row-by-row procedure.

    SELECT name, city
    FROM customers
    WHERE city = 'Delhi'
    ORDER BY name;

## Filtering

WHERE filters rows before grouping. Common operators include =, <>, BETWEEN, IN, LIKE, IS NULL and comparison operators. NULL represents missing or unknown data; use IS NULL rather than = NULL.

## Sorting and limiting

ORDER BY can sort by multiple columns. LIMIT restricts the number of returned rows in SQLite. Add a stable tie-breaker to ORDER BY when reproducible ordering matters.

## Logical query processing

A useful conceptual order is FROM/JOIN, WHERE, GROUP BY, HAVING, SELECT, DISTINCT, ORDER BY, LIMIT. It explains why a SELECT alias is not always available in WHERE.

## Practice

1. List delivered orders above a chosen amount.
2. Find customers whose city is missing.
3. Return the three highest-paid employees with a deterministic tie-breaker.
4. Count orders by status."""),
            ("joins-and-aggregation", "Joins, GROUP BY and HAVING", 22, """## Joins

An INNER JOIN returns matching row pairs. A LEFT JOIN keeps every row from the left relation and fills right-side columns with NULL when there is no match.

    SELECT c.name, o.order_id, o.amount
    FROM customers AS c
    LEFT JOIN orders AS o
      ON o.customer_id = c.customer_id;

Join on the correct relationship keys. Joining tables without a valid condition can multiply rows and inflate aggregates.

## Aggregation

COUNT counts rows (COUNT(*) includes rows regardless of NULL columns); COUNT(column) excludes NULL values. SUM, AVG, MIN and MAX summarize values. GROUP BY creates one output group per key combination.

HAVING filters groups after aggregation; WHERE filters individual rows before aggregation.

## Practice

1. Show total delivered spend per customer.
2. Find departments whose average salary exceeds a threshold.
3. List customers with no orders using LEFT JOIN and a NULL check.
4. Explain why joining order items to orders can change row counts."""),
            ("subqueries-and-ctes", "Subqueries and common table expressions", 20, """## Subqueries

A subquery is a query nested inside another query. It may return a scalar value, a list of values or a relation. EXISTS tests whether at least one matching row exists and is often useful for semi-join logic.

    SELECT name
    FROM customers c
    WHERE EXISTS (
      SELECT 1 FROM orders o
      WHERE o.customer_id = c.customer_id
    );

## Common table expressions

A CTE names a query result for use by the statement that follows. It can make multi-step transformations easier to read.

    WITH customer_totals AS (
      SELECT customer_id, SUM(amount) AS total_amount
      FROM orders
      WHERE status = 'delivered'
      GROUP BY customer_id
    )
    SELECT customer_id, total_amount
    FROM customer_totals
    WHERE total_amount > 1000;

A CTE is not automatically a materialized temporary table; the query planner decides how to execute it.

## Practice

1. Find employees paid above the overall average.
2. Use a CTE to calculate each customer's delivered spend.
3. Find customers who have at least one pending order.
4. Rewrite a nested query as a CTE and compare readability."""),
            ("window-functions", "Window functions and ranking", 24, """## Window function concept

A window function computes a value across related rows without collapsing them into one row per group. The OVER clause defines the window; PARTITION BY restarts the calculation for each group, and ORDER BY defines row order inside that group.

    SELECT department_id, name, salary,
           ROW_NUMBER() OVER (
             PARTITION BY department_id
             ORDER BY salary DESC, employee_id
           ) AS row_num
    FROM employees;

ROW_NUMBER assigns unique sequential numbers. RANK leaves gaps after ties; DENSE_RANK does not leave gaps. Choose a deterministic tie-breaker when one row must rank first.

Aggregate window functions such as SUM(salary) OVER (PARTITION BY department_id) show group totals alongside individual rows.

## Practice

1. Rank salaries within each department.
2. Return the highest-paid employee per department.
3. Calculate a running total of orders by date.
4. Explain the difference between ROW_NUMBER, RANK and DENSE_RANK."""),
        ],
    },
    {
        "title": "DSA Foundations",
        "slug": "dsa-foundations",
        "category": "dsa",
        "difficulty": "beginner",
        "description": "Learn how to reason about complexity and build core problem-solving patterns.",
        "lessons": [
            ("complexity-basics", "Time and space complexity", 18, """## Why complexity matters

Complexity describes how resource use grows as input size n grows. Big-O focuses on the dominant growth term and ignores constants and lower-order terms.

Common growth rates include O(1), O(log n), O(n), O(n log n), O(n²) and O(2ⁿ). A single loop over n items is usually O(n); two nested loops over n items are often O(n²).

## Auxiliary space

Auxiliary space describes additional memory used by an algorithm, not necessarily the input itself. A new list of n values is O(n) extra space; a few pointers and counters are O(1).

## Analyse carefully

Not every nested loop is O(n²): two pointers that each move forward at most n times can be O(n) total. Likewise, a loop that halves its search interval is O(log n).

## Practice

1. State the time complexity of membership search in a Python list and a set.
2. Analyse a loop that doubles i from 1 while i < n.
3. Explain why sorting followed by a linear scan is usually O(n log n).
4. Count the additional memory used by a frequency dictionary."""),
            ("hashing-pattern", "Hash maps and frequency counting", 20, """## Hashing pattern

A dictionary maps keys to values. A set stores unique keys. They are useful when the question asks about membership, duplicates, counts, pairs or grouping.

    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1

Dictionary and set operations are average O(1), but this is an average-case statement, not a guarantee for every adversarial or pathological input.

## Two Sum reasoning

For each current value x, the complement is target - x. Check whether that complement was seen earlier; if so, return the two indices. Otherwise store x and its index.

Checking before inserting prevents accidentally using the same element twice.

## Practice

1. Count frequencies of integers.
2. Detect whether a list contains duplicates.
3. Find the first non-repeating character.
4. Solve Two Sum and explain why the dictionary approach is linear on average."""),
            ("two-pointers", "Two pointers and sliding windows", 20, """## Two pointers

Two pointers maintain positions in a sequence. For a sorted pair-sum problem, compare nums[left] + nums[right] with the target and move the pointer that can improve the sum.

The sorted order is important: moving left increases the sum; moving right decreases it.

## Sliding window

A sliding window maintains a contiguous range. For a fixed-size window, remove the outgoing item and add the incoming item. For a variable-size window, grow and shrink the boundaries while maintaining an invariant.

Do not apply a simple expand/shrink window to arbitrary negative-number subarray-sum problems without proving the invariant; negative values can break monotonicity.

## Practice

1. Reverse a string in place using two pointers.
2. Merge two sorted arrays.
3. Find a maximum sum window of length k.
4. Find the longest substring without repeated characters.
5. Explain when a sliding window is not suitable."""),
        ],
    },
    {
        "title": "Data Engineering Essentials",
        "slug": "data-engineering-essentials",
        "category": "data-engineering",
        "difficulty": "beginner",
        "description": "Understand the building blocks of reliable batch data pipelines.",
        "lessons": [
            ("etl-pipeline", "ETL and data pipeline fundamentals", 20, """## Pipeline stages

A typical batch pipeline extracts data from a source, validates and transforms it, and loads it into a destination. Keep each stage observable and retryable.

## Reliability

Design jobs to be idempotent where possible: rerunning a job should not create duplicate business facts. Use stable business keys, deterministic transformations, checkpointing and safe upserts.

Keep raw source data separately from curated outputs so that transformation logic can be corrected and rerun.

## Data quality

Check required fields, types, accepted ranges, duplicates, referential integrity and freshness. Record rejected rows with reason codes instead of silently dropping them.

## Practice

1. Design a CSV-to-database ingestion flow.
2. Define five quality checks for an orders dataset.
3. Explain how you would prevent duplicate rows after a retry.
4. Describe the difference between a batch and a streaming pipeline."""),
            ("data-modelling", "Facts, dimensions and data grain", 22, """## Start with grain

The grain states what one row in a fact table represents. A fact_order_items table might have one row per order line. Measures must be defined at that grain and aggregated without double counting.

## Facts and dimensions

Fact tables store measurable events and foreign keys to descriptive dimensions. Dimension tables provide customer, product, location or date context.

A star schema separates facts from dimensions to make analytics queries understandable. Slowly changing dimensions preserve historical attribute values when business reporting needs the state as of an earlier time.

## Practice

1. Define the grain for an order-line fact table.
2. Distinguish an additive measure from a non-additive ratio.
3. Explain when a customer attribute needs historical tracking.
4. Sketch fact and dimension relationships for a small retail model."""),
            ("batch-and-streaming", "Batch, streaming and orchestration", 20, """## Batch and streaming

Batch processing handles a bounded set of records on a schedule or trigger. Streaming systems process continuously arriving events and require attention to event time, late data, ordering, duplicates and delivery guarantees.

## Orchestration

An orchestrator coordinates tasks, dependencies, retries, schedules, parameters and observability. A task should be small, testable and safe to retry.

## Tools and trade-offs

Spark is used for distributed data processing; Kafka is a distributed event log commonly used for event streaming; Airflow is a workflow orchestrator. A tool should be selected to solve a real scale, latency or operational requirement, not simply added to a résumé.

## Practice

1. Choose batch or streaming for a nightly payroll report and justify it.
2. Explain how to handle a late arriving event.
3. Design retry behaviour for a failed daily extract.
4. Describe the responsibilities of Kafka, Spark and Airflow."""),
        ],
    },

    {
        "title": "Python Libraries for Data Work",
        "slug": "python-libraries-data",
        "category": "libraries",
        "difficulty": "beginner",
        "description": "Practise NumPy, Pandas, data cleaning and reliable API extraction.",
        "lessons": [
            ("numpy-arrays", "NumPy arrays and vectorization", 20, """## NumPy arrays

NumPy provides homogeneous n-dimensional arrays and vectorized operations. Arrays are useful for numeric workloads because operations can run in optimized compiled code.

    import numpy as np
    values = np.array([10, 20, 30])
    print(values.mean())
    print(values * 2)

An array's shape describes its dimensions. reshape changes the shape when the element count remains compatible. Broadcasting lets compatible shapes participate in element-wise operations.

## Indexing and views

Basic slicing often returns a view, so modifying a slice may affect the original array. Fancy indexing generally creates a copy. Be deliberate about this distinction when changing data.

## Practice

1. Create a 3 by 3 array and calculate row sums.
2. Normalize a vector by its maximum.
3. Reshape 12 values into a 3 by 4 matrix.
4. Explain the difference between a Python list and a NumPy array."""),
            ("pandas-cleaning", "Pandas DataFrames and data cleaning", 24, """## Inspect before transforming

A Series is a labelled one-dimensional structure. A DataFrame is a labelled table. Start by inspecting head(), info(), describe(), isna().sum() and duplicated().sum().

    import pandas as pd
    df = pd.read_csv("sales.csv")
    df = df.drop_duplicates()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

Do not fill missing values blindly. Decide based on what the field means, preserve a record of the decision and validate the resulting row counts.

## Grouping and joins

groupby() supports grouped aggregation. merge() joins DataFrames by keys. Check the expected key uniqueness and row counts after joins to catch accidental row multiplication.

## Practice

1. Load a CSV and inspect missing values and data types.
2. Remove duplicate order IDs.
3. Group revenue by month and product category.
4. Merge customer and order records and explain the join cardinality.
5. Export a cleaned DataFrame without its index."""),
            ("requests-and-json", "Requests, REST APIs and JSON", 20, """## HTTP requests

Requests sends HTTP calls. GET usually retrieves a resource; POST usually submits data. Check status codes, parse JSON only when the response contains JSON, and always configure timeouts.

    import requests
    response = requests.get("https://api.example.com/items", timeout=10)
    response.raise_for_status()
    payload = response.json()

## Robust extraction

APIs may paginate, rate-limit, require authentication or temporarily fail. Use bounded retries for safe operations, respect rate-limit headers and record extraction timestamps and source identifiers.

Never commit API keys into source code or frontend bundles. Read secrets from environment variables or a secret manager.

## Practice

1. Parse a nested JSON response.
2. Write a helper that handles non-2xx responses.
3. Explain offset pagination versus cursor pagination.
4. Design an API-to-CSV extraction workflow."""),
        ],
    },
    {
        "title": "Core Computer Science",
        "slug": "core-computer-science",
        "category": "core-cs",
        "difficulty": "beginner",
        "description": "Revise DBMS, operating systems and computer networks for technical interviews.",
        "lessons": [
            ("dbms-keys-normalization", "DBMS keys and normalization", 22, """## Keys and relationships

A super key uniquely identifies a row. A candidate key is a minimal super key. A primary key is the chosen candidate key. A foreign key references a key in another table and helps enforce referential integrity.

## Functional dependencies

A functional dependency X -> Y means X determines Y. Normalization reduces update, insert and delete anomalies by organizing attributes around dependencies.

First normal form requires atomic values. Second normal form removes partial dependency on a proper subset of a candidate key. Third normal form removes relevant transitive dependencies of non-key attributes.

## Transactions and ACID

Atomicity, consistency, isolation and durability describe transaction properties. Isolation levels trade concurrency against phenomena such as dirty reads and non-repeatable reads.

## Practice

1. Identify candidate keys in an order-line relation.
2. Explain why storing many product IDs in one delimited column is problematic.
3. Describe an update anomaly.
4. Explain what a foreign key prevents."""),
            ("os-processes-memory", "Operating systems: processes and memory", 22, """## Processes and threads

A process is a running program with its own address space and resources. Threads within a process share address space, while each thread has its own execution state and stack.

Context switching saves and restores execution state. Too many runnable threads can increase scheduling overhead.

## Virtual memory

Virtual memory provides each process with an abstract address space. Paging maps virtual pages to physical frames. A page fault occurs when an access cannot be satisfied by the current page mappings.

## Deadlocks and synchronization

The four Coffman conditions are mutual exclusion, hold and wait, no preemption and circular wait. Deadlock prevention breaks at least one necessary condition. Locks protect shared state but must be acquired consistently to avoid deadlocks.

## Practice

1. Compare process and thread isolation.
2. Explain the purpose of virtual memory.
3. Describe a race condition and how a lock helps.
4. List the four necessary deadlock conditions."""),
            ("computer-networks", "Computer networks and web protocols", 22, """## Network layers

The OSI model describes seven conceptual layers. TCP/IP is the practical protocol suite used by the internet. Layering helps separate application behaviour from transport and network delivery.

## TCP and UDP

TCP provides a reliable ordered byte stream with connection management and congestion control. UDP provides datagrams without TCP's delivery guarantees; applications may add their own reliability.

## HTTP and DNS

DNS maps names to records such as IP addresses. HTTP defines request and response semantics. HTTPS is HTTP protected by TLS, which provides confidentiality and integrity and authenticates the server when certificate validation succeeds.

## Practice

1. Trace what happens after entering a hostname in a browser.
2. Compare TCP and UDP use cases.
3. Explain why HTTP 404 differs from 500.
4. Describe the role of TLS."""),
        ],
    },
    {
        "title": "Aptitude and Logical Reasoning",
        "slug": "aptitude-logical-reasoning",
        "category": "aptitude",
        "difficulty": "beginner",
        "description": "Practise percentages, ratios, time-work problems and logical deduction.",
        "lessons": [
            ("percentages-ratios-averages", "Percentages, ratios and averages", 20, """## Percentages

x percent of value v is (x / 100) × v. A percentage increase followed by a percentage decrease is applied to the current value, not automatically to the original value.

## Ratios

If a:b = 2:3, quantities can be written as 2k and 3k. Use the known total or difference to solve for k.

## Averages

Average is total divided by count. When combining groups with different sizes, use a weighted average rather than averaging the group averages directly.

## Practice

1. Find 18% of 450.
2. Divide 720 in the ratio 2:3:4.
3. The average of five values is 16. Find their total.
4. A value rises by 20% and then falls by 20%. Explain why it does not return to its initial value."""),
            ("time-work-speed", "Time, work and speed", 22, """## Work rates

If a worker completes one job in a days, the constant work rate is 1/a jobs per day. For independent workers operating together, add their rates, not their completion times.

## Speed, distance and time

Distance = speed × time. Keep units consistent. Convert km/h to m/s by multiplying by 5/18.

For two objects moving in opposite directions, relative speed is the sum of their speeds. For the same direction, it is the absolute difference.

## Practice

1. A completes a task in 6 days and B in 3 days. Find their joint time.
2. Convert 72 km/h to m/s.
3. Two trains approach each other; calculate relative speed.
4. Explain the difference between average speed and average of speeds."""),
            ("logical-deduction", "Logical series and deduction", 18, """## Number series

Look for first differences, second differences, ratios, alternating sequences and repeated operations. Test a proposed pattern against every provided term.

## Syllogisms

Translate statements into sets. A conclusion is valid only when it follows necessarily from the premises. Do not use outside assumptions.

## Directions and arrangements

For direction questions, use a coordinate sketch. For seating arrangements, encode each condition separately and eliminate contradictions systematically.

## Practice

1. Find the next term in 2, 6, 12, 20, 30.
2. Draw a direction path and compute final displacement.
3. Check whether a conclusion follows from two set-inclusion statements.
4. Solve a small seating arrangement by constructing a table."""),
        ],
    },
    {
        "title": "AI and Machine Learning Fundamentals",
        "slug": "ai-ml-fundamentals",
        "category": "ai-ml",
        "difficulty": "beginner",
        "description": "Understand the machine-learning workflow, model types and evaluation.",
        "lessons": [
            ("ml-workflow-and-splits", "Machine-learning workflow and data splits", 22, """## Define the problem

Identify the prediction target, unit of observation, business objective, data availability and cost of errors. Decide whether the task is regression, classification, ranking, clustering or another problem type.

## Split data correctly

Separate training, validation and test data. Fit preprocessing only on training data, then apply the fitted transformation to validation and test data. This prevents information leakage.

For time-dependent data, use a time-aware split rather than randomly mixing future and past observations.

## Baselines and reproducibility

Start with a simple baseline. Record data versions, model settings and evaluation metrics. A complex model is useful only when it improves a meaningful metric on held-out data.

## Practice

1. Define features and target for house-price prediction.
2. Explain why preprocessing before the train/test split leaks information.
3. Choose a time-based split for monthly demand data.
4. Propose a simple baseline."""),
            ("classification-metrics", "Classification, regression and evaluation", 22, """## Regression

Regression predicts a numeric target. Linear regression models a weighted combination of features. MAE reports average absolute error; RMSE penalizes larger errors more strongly.

## Classification

Classification predicts categories. Logistic regression estimates class probabilities. Decision trees split feature space into regions. Random forests combine many trees to reduce variance.

## Metrics

Accuracy can be misleading with imbalanced classes. Precision asks what fraction of predicted positives are correct; recall asks what fraction of actual positives are found. F1 combines precision and recall using their harmonic mean. Use a confusion matrix to inspect error types.

## Practice

1. Pick a metric for a rare-fraud detector and justify it.
2. Explain false positives versus false negatives.
3. Compare MAE and RMSE.
4. Explain why accuracy may mislead on imbalanced data."""),
            ("overfitting-feature-engineering", "Overfitting and feature engineering", 20, """## Generalization

A model overfits when it captures patterns specific to training data and performs poorly on unseen observations. A large gap between training and validation performance can be a warning sign.

## Reduce overfitting

Use simpler models, regularization, early stopping, representative data or cross-validation. Choose settings on validation data; keep the test set for final evaluation.

## Feature engineering

Features must be available at prediction time and must not leak target or future information. Handle missing values, categories, outliers and dates in a reproducible pipeline.

## Practice

1. Identify a possible leakage feature in a credit-risk task.
2. Explain L1 versus L2 regularization at a high level.
3. Decide whether random K-fold is suitable for time-series forecasting.
4. Suggest date-derived features for demand prediction."""),
        ],
    },

]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for course_data in COURSES:
            lessons = course_data["lessons"]
            course_fields = {k: v for k, v in course_data.items() if k != "lessons"}
            course = db.scalar(select(Course).where(Course.slug == course_fields["slug"]))
            if course is None:
                course = Course(**course_fields)
                db.add(course)
                db.flush()
            for index, (slug, title, minutes, content) in enumerate(lessons, start=1):
                existing = db.scalar(select(Lesson).where(
                    Lesson.course_id == course.id, Lesson.slug == slug
                ))
                if existing is None:
                    db.add(Lesson(
                        course_id=course.id,
                        slug=slug,
                        title=title,
                        content=content,
                        estimated_minutes=minutes,
                        display_order=index,
                        is_published=True,
                    ))
        db.commit()


if __name__ == "__main__":
    seed()
