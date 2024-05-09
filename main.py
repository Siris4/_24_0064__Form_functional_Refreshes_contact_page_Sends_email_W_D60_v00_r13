from flask import Flask, render_template, request
import datetime as dt
import requests
import re
import smtplib
import os
import logging

app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MY_NAME = 'Gavin "Siris" Martin'  # Defined globally for reuse in routes and/or functions

# Environment variables for email configuration
my_from_email1 = os.environ.get('MY_FROM_EMAIL1', 'Custom Message / Email does not exist')
password = os.environ.get('PASSWORD', 'Custom Message / Password does not exist')
their_email2 = os.environ.get('THEIR_EMAIL2', 'Custom Message / Email does not exist')

# Context processor to inject variables into all templates
@app.context_processor
def inject_globals():
    return {
        'CURRENT_YEAR': dt.datetime.now().year,
        'MY_NAME': MY_NAME
    }

# Function to clean and slugify input strings
def slugify(value):
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[\s_-]+', '-', value)
    return value

app.jinja_env.filters['slugify'] = slugify

# Function to fetch posts and handle images based on post titles
def fetch_posts():
    static_posts = [{"title": "All About Llamas", "subtitle": "One of the South American members of Camelidae",
                     "author": "Mojo Jojo", "date": "2023-09-24", "image": "llama.jpg",
                     "body": "The llama is the largest of the four lamoid species. It averages 120 cm (47 inches) at the shoulder, with most males weighing between 136 and 181.4 kg (300 and 400 pounds) and most females weighing between 104.3 and 158.7 kg (230 and 350 pounds). A 113-kg (250-pound) llama can carry a load of 45–60 kg and average 25 to 30 km (15 to 20 miles) travel a day. The llama’s high thirst tolerance, endurance, and ability to subsist on a wide variety of forage makes it an important transport animal on the bleak Andean plateaus and mountains. The llama is a gentle animal, but, when overloaded or maltreated, it will lie down, hiss, spit and kick, and refuse to move. Llamas breed in the (Southern Hemispheric) late summer and fall, from November to May. The gestation period lasts about 11 months, and the female gives birth to one young. Although usually white, the llama may be solid black or brown, or it may be white with black or brown markings."}]
    try:
        blog_url = "https://api.npoint.io/e52811763db21dfef489"
        blog_response = requests.get(blog_url)
        blog_response.raise_for_status()
        api_posts = blog_response.json()
        update_post_images(api_posts)
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve blog data: {e}")
        api_posts = []
    return static_posts + api_posts

def update_post_images(api_posts):
    for post in api_posts:
        post['date'] = dt.datetime.now().strftime("%b %d, %Y %I:%M%p")
        post['author'] = post.get('author', 'Dr. Angela Yu')
        post['image'] = post.get('image', 'default.jpg')
        if 'explore' in post['title'].lower():
            post['image'] = 'explore.jpg'
        elif 'heart' in post['title'].lower():
            post['image'] = 'heart2.jpg'
        elif 'science' in post['title'].lower():
            post['image'] = 'science.jpg'
        elif 'failure' in post['title'].lower():
            post['image'] = 'failure.jpg'

@app.route('/')
@app.route('/home')
def home():
    all_posts = fetch_posts()
    all_posts.sort(key=lambda x: x['date'], reverse=True)
    return render_template("index.html", posts=all_posts, page='home')

@app.route('/post/<slug>')
def post(slug):
    all_posts = fetch_posts()
    post = next((p for p in all_posts if slugify(p['title']) == slug), None)
    if post is None:
        return "Post not found", 404
    return render_template("post.html", post=post)

@app.route('/about')
def about():
    return render_template('about.html', page='about')

@app.route('/contact', methods=["GET", "POST"])
def contact():
    form_submitted = False
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        if validate_input(name, email, phone, message):
            send_email(name, email, phone, message)
            form_submitted = True
            logging.info(f"Contact form submitted: {name}, {email}")
        else:
            logging.warning("Validation failed for contact form submission.")
            return "Invalid input data", 400
    return render_template("contact.html", form_submitted=form_submitted)

def validate_input(name, email, phone, message):
    if not all([name, email, phone, message]):
        return False
    if "@" not in email or "." not in email:  # Simple email validation
        return False
    return True

def send_email(name, email, phone, message):
    """ Function to send email with contact details. """
    email_subject = "New Contact Form Submission for Siris's Blog"
    email_body = f"Subject:{email_subject}\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
    try:
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=my_from_email1, password=password)
            connection.sendmail(
                from_addr=my_from_email1,
                to_addrs=their_email2,
                msg=email_body
            )
        logging.info("Email sent successfully")
    except smtplib.SMTPException as e:
        logging.error(f"Failed to send email: {e}")

if __name__ == "__main__":
    app.run(debug=True)
