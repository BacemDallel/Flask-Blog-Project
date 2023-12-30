Project Title: Simple Blogging Website with Flask

Description:

This project is a simple blogging website developed using Flask, a Python-based web framework. It allows users to create, view, edit, and delete blog posts. The website utilizes SQLAlchemy for managing a SQLite database to store blog post information.

Key Features:

Create Posts: Users can create new blog posts by providing a title, subtitle, author name, an image URL, and the main content of the post using a rich text editor powered by CKEditor.

View Posts: All existing blog posts are displayed on the homepage, showcasing the title, author, and creation date. Users can click on a post to view its full content.

Edit Posts: Users can edit existing blog posts, modifying the title, subtitle, author, image URL, and content. The posts are edited using a similar form used for creating new posts.

Delete Posts: Posts can be deleted by users, removing them from the database.

Technologies Used:

Flask: A lightweight web framework for Python used to build the web application.

SQLAlchemy: An ORM (Object-Relational Mapping) library for Python, employed for database management.

Flask-WTF: Used for handling web forms and input validation.

Flask-CKEditor: Integrated for providing a rich text editor for creating and editing blog post content.

Bootstrap5: A front-end framework utilized for creating responsive and visually appealing web pages.

SQLite: A relational database management system employed to store blog post data.

Usage:

The application can be accessed through a web browser. Users can navigate to different sections of the site such as the homepage to view all posts, view individual posts, create new posts, edit existing posts, and delete posts.

