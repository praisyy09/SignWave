import json
import os
# from nltk.parse import stanford
"""from pyngrok import ngrok"""
from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_session import Session
from pymongo import MongoClient
import bcrypt
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess

# Define a route for the app

import stanza 
stanza.download('en',model_dir='stanza_resources')
# stanza.install_corenlp()
# from nltk.stem import WordNetLemmatizer
# from nltk.tokenize import word_tokenize
# from nltk.tokenize import sent_tokenize
# from nltk.corpus import stopwords
from nltk.parse.stanford import StanfordParser
from nltk.tree import *
from six.moves import urllib
import zipfile
import sys
import time
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
from flask import Flask,request,render_template,send_from_directory,jsonify

app =Flask(__name__,static_folder='static', static_url_path='')

import stanza
# from stanza.server import CoreNLPClient
import pprint 


# These few lines are important
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# Download zip file from https://nlp.stanford.edu/software/stanford-parser-full-2018-10-17.zip and extract in stanford-parser-full-2015-04-20 folder in higher directory
os.environ['CLASSPATH'] = os.path.join(BASE_DIR, 'stanford-parser-full-2018-10-17')
os.environ['STANFORD_MODELS'] = os.path.join(BASE_DIR,
                                             'stanford-parser-full-2018-10-17/edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz')
os.environ['NLTK_DATA'] = '/usr/local/share/nltk_data/'


from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_session import Session
from pymongo import MongoClient
import bcrypt
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
# Initialize session
app.config['SECRET_KEY'] = '5a16ea28a83abdec453114311ac5d93f'  # Set your own secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)  # Initialize session

# Initialize MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["signwave"]  # Replace with your database name
users_collection = db["signwave"]  # Replace with your collection name

# Placeholder for hash_password function
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

@app.route('/')
def home():
    return render_template('home.html')  # Home page with login and signup buttons

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        today_date = time.strftime("%Y-%m-%d")

        
        
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return redirect(url_for('signup'))
        
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            flash("Email already registered. Please login.", "danger")
             
            return redirect(url_for('signup'))
        
        hashed_password = hash_password(password)
        user = {
            "name": name,
            "email": email,
            
            "password": hashed_password,
            "day": [today_date],
            "count": [0]
        }
        users_collection.insert_one(user)
        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/run_script', methods=['GET'])
def run_script():
    # Run the final_predict.py script
    try:
        subprocess.Popen([sys.executable, 'final_pred.py'])
        return jsonify({"status": "success", "message": "Script is running"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Function to check passwords
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8') if isinstance(hashed, str) else hashed)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """if 'email' in session:
        return redirect(url_for('index1'))"""
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = users_collection.find_one({"email": email})
        
        if user and check_password(password, user['password']):
            session['email'] = email  # Store email in session
            
            # Generate and send OTP
            otp = generate_otp()
            session["otp"] = otp  # Store OTP in session
            if send_otp_email(email, otp):
                flash("OTP sent to your email. Please check.", "success")
                return redirect(url_for('otp_verification'))
            else:
                flash("Failed to send OTP. Try again.", "danger")
                return redirect(url_for('login'))
        else:
            flash("Invalid email or password", "danger")
    
    return render_template('login.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = users_collection.find_one({"email": email})
        
        if user:
            # Generate and send OTP or reset link
            otp = generate_otp()
            session["reset_otp"] = otp  # Store OTP in session
            session["reset_email"] = email  # Store email in session
            
            if send_otp_email(email, otp):
                flash("An OTP has been sent to your email. Please check.", "success")
                return redirect(url_for('reset_password_otp'))
            else:
                flash("Failed to send OTP. Please try again.", "danger")
        else:
            flash("Email not registered. Please sign up.", "danger")
    
    return render_template('forgot_password.html')
@app.route('/sigtotext')
def sigtotext():
    return render_template('sigtotext.html')


@app.route('/reset_password_otp', methods=['GET', 'POST'])
def reset_password_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        actual_otp = session.get("reset_otp")
        
        if actual_otp and entered_otp == str(actual_otp):  # Compare as string
            session.pop("reset_otp")  # Clear OTP from session
            return redirect(url_for('reset_password'))  # Redirect to reset password form
        else:
            flash("Invalid OTP, please try again.", "danger")
    
    return render_template('reset_password_otp.html')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        email = session.get("reset_email")  # Retrieve email from session
        
        if new_password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return redirect(url_for('reset_password'))
        
        if email:
            hashed_password = hash_password(new_password)
            users_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})
            session.pop("reset_email")  # Clear email from session
            flash("Password reset successful! Please log in.", "success")
            return redirect(url_for('login'))
    
    return render_template('reset_password.html')


# Function to generate OTP
def generate_otp():
    otp = random.randint(1000, 9999)
    return otp

# Function to send OTP email
def send_otp_email(email, otp):
    sender_email = "nikhathmahammad12@gmail.com"
    sender_password = "yhos ywhn elzt rucx"
    receiver_email = email
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    return True

@app.route('/otp_verification', methods=['POST', 'GET'])
def otp_verification():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        actual_otp = session.get("otp")  # Get stored OTP from session

        if actual_otp and entered_otp == str(actual_otp):  # Compare as string
            session.pop("otp")  # Remove OTP from session after verification
            return redirect(url_for('index1'))
        else:
            flash("Invalid OTP, try again.", "danger")

    return render_template('otp_verification.html')
@app.route('/index1')  # Index page route
def index1():
     # Redirect to login page if not logged in
    return render_template('index1.html')  

@app.route('/index',methods=['GET'])  # Index page route
def index():
    """if 'email' not in session:
        return redirect(url_for('login'))"""  # Redirect to login page if not logged in
    clear_all()
    
    return redirect("https://658f-2401-4900-4feb-dfd-35d1-b161-8934-e204.ngrok-free.app/")  # Home page with login and signup buttons

@app.route('/profile')
def profile():
    if 'email' not in session:  
        return redirect(url_for('login'))
    email = session.get('email')  # Get email from session
    user = users_collection.find_one({"email": email})
    if user:
        return render_template('profile.html', user=user)  # Pass user data to the template
    return redirect(url_for('login'))  # Redirect to login if email is not provided

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']  # Get email from session
    user = users_collection.find_one({"email": email})  # Fetch user data from the database

    if request.method == 'POST':
        # Update user details
        updated_name = request.form['name']
       

        users_collection.update_one(
            {"email": email},
            {"$set": {
                "name": updated_name,
                
            }}
        )

        # Redirect back to profile with updated details
        return redirect(url_for('profile'))

    # Render the edit profile page
    return render_template('edit_profile.html', user=user)

@app.route('/logout')  
def logout():
    session.pop('email', None)  
    return redirect(url_for('index'))



# checks if jar file of stanford parser is present or not
def is_parser_jar_file_present():
    stanford_parser_zip_file_path = os.environ.get('CLASSPATH') + ".jar"
    return os.path.exists(stanford_parser_zip_file_path)


def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.perf_counter()
        return
    duration = time.perf_counter() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = min(int(count*block_size*100/total_size),100)
    sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                    (percent, progress_size / (1024 * 1024), speed, duration))
    sys.stdout.flush()

# downloads stanford parser
def download_parser_jar_file():
    stanford_parser_zip_file_path = os.environ.get('CLASSPATH') + ".jar"
    url = "https://nlp.stanford.edu/software/stanford-parser-full-2018-10-17.zip"
    urllib.request.urlretrieve(url, stanford_parser_zip_file_path, reporthook)

# extracts stanford parser
def extract_parser_jar_file():
    stanford_parser_zip_file_path = os.environ.get('CLASSPATH') + ".jar"
    try:
        with zipfile.ZipFile(stanford_parser_zip_file_path) as z:
            z.extractall(path=BASE_DIR)
    except Exception:
        os.remove(stanford_parser_zip_file_path)
        download_parser_jar_file()
        extract_parser_jar_file()

# extracts models of stanford parser
def extract_models_jar_file():
    stanford_models_zip_file_path = os.path.join(os.environ.get('CLASSPATH'), 'stanford-parser-3.9.2-models.jar')
    stanford_models_dir = os.environ.get('CLASSPATH')
    with zipfile.ZipFile(stanford_models_zip_file_path) as z:
        z.extractall(path=stanford_models_dir)


# checks jar file and downloads if not present 
def download_required_packages():
    if not os.path.exists(os.environ.get('CLASSPATH')):
        if is_parser_jar_file_present():
           pass
        else:
            download_parser_jar_file()
        extract_parser_jar_file()

    if not os.path.exists(os.environ.get('STANFORD_MODELS')):
        extract_models_jar_file()






# Pipeline for stanza (calls spacy for tokenizer)
en_nlp = stanza.Pipeline('en',processors={'tokenize':'spacy'})	
# print(stopwords.words('english'))

# stop words that are not to be included in ISL
stop_words = set(["am","are","is","was","were","be","being","been","have","has","had",
					"does","did","could","should","would","can","shall","will","may","might","must","let","the","a"]);



# sentences array
sent_list = [];
# sentences array with details provided by stanza
sent_list_detailed=[];

# word array
word_list=[];

# word array with details provided by stanza 
word_list_detailed=[];

# converts to detailed list of sentences ex. {"text":"word","lemma":""}
def convert_to_sentence_list(text):
	for sentence in text.sentences:
		sent_list.append(sentence.text)
		sent_list_detailed.append(sentence)


# converts to words array for each sentence. ex=[ ["This","is","a","test","sentence"]];
def convert_to_word_list(sentences):
	temp_list=[]
	temp_list_detailed=[]
	for sentence in sentences:
		for word in sentence.words:
			temp_list.append(word.text)
			temp_list_detailed.append(word)
		word_list.append(temp_list.copy())
		word_list_detailed.append(temp_list_detailed.copy())
		temp_list.clear();
		temp_list_detailed.clear();


# removes stop words
def filter_words(word_list):
	temp_list=[];
	final_words=[];
	# removing stop words from word_list
	for words in word_list:
		temp_list.clear();
		for word in words:
			if word not in stop_words:
				temp_list.append(word);
		final_words.append(temp_list.copy());
	# removes stop words from word_list_detailed 
	for words in word_list_detailed:
		for i,word in enumerate(words):
			if(words[i].text in stop_words):
				del words[i];
				break;
	
	return final_words;
# 

# removes punctutation 
def remove_punct(word_list):
	# removes punctutation from word_list_detailed
	for words,words_detailed in zip(word_list,word_list_detailed):
		for i,(word,word_detailed) in enumerate(zip(words,words_detailed)):
			if(word_detailed.upos=='PUNCT'):
				del words_detailed[i];
				words.remove(word_detailed.text);
				break;


# lemmatizes words
def lemmatize(final_word_list):
	for words,final in zip(word_list_detailed,final_word_list):
		for i,(word,fin) in enumerate(zip(words,final)):
			if fin in word.text:
				if(len(fin)==1):
					final[i]=fin;
				else:
					final[i]=word.lemma;
				
	
	for word in final_word_list:
		print("final_words",word);

def label_parse_subtrees(parent_tree):
    tree_traversal_flag = {}

    for sub_tree in parent_tree.subtrees():
        tree_traversal_flag[sub_tree.treeposition()] = 0
    return tree_traversal_flag



# handles if noun is in the tree
def handle_noun_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree):
    # if clause is Noun clause and not traversed then insert them in new tree first
    if tree_traversal_flag[sub_tree.treeposition()] == 0 and tree_traversal_flag[sub_tree.parent().treeposition()] == 0:
        tree_traversal_flag[sub_tree.treeposition()] = 1
        modified_parse_tree.insert(i, sub_tree)
        i = i + 1
    return i, modified_parse_tree


# handles if verb/proposition is in the tree followed by nouns
def handle_verb_prop_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree):
    # if clause is Verb clause or Proportion clause recursively check for Noun clause
    for child_sub_tree in sub_tree.subtrees():
        if child_sub_tree.label() == "NP" or child_sub_tree.label() == 'PRP':
            if tree_traversal_flag[child_sub_tree.treeposition()] == 0 and tree_traversal_flag[child_sub_tree.parent().treeposition()] == 0:
                tree_traversal_flag[child_sub_tree.treeposition()] = 1
                modified_parse_tree.insert(i, child_sub_tree)
                i = i + 1
    return i, modified_parse_tree


# modifies the tree according to POS
def modify_tree_structure(parent_tree):
    # Mark all subtrees position as 0
    tree_traversal_flag = label_parse_subtrees(parent_tree)
    # Initialize new parse tree
    modified_parse_tree = Tree('ROOT', [])
    i = 0
    for sub_tree in parent_tree.subtrees():
        if sub_tree.label() == "NP":
            i, modified_parse_tree = handle_noun_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree)
        if sub_tree.label() == "VP" or sub_tree.label() == "PRP":
            i, modified_parse_tree = handle_verb_prop_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree)

    # recursively check for omitted clauses to be inserted in tree
    for sub_tree in parent_tree.subtrees():
        for child_sub_tree in sub_tree.subtrees():
            if len(child_sub_tree.leaves()) == 1:  #check if subtree leads to some word
                if tree_traversal_flag[child_sub_tree.treeposition()] == 0 and tree_traversal_flag[child_sub_tree.parent().treeposition()] == 0:
                    tree_traversal_flag[child_sub_tree.treeposition()] = 1
                    modified_parse_tree.insert(i, child_sub_tree)
                    i = i + 1

    return modified_parse_tree

# converts the text in parse trees
def reorder_eng_to_isl(input_string):
	download_required_packages();
	# check if all the words entered are alphabets.
	count=0
	for word in input_string:
		if(len(word)==1):
			count+=1;

	if(count==len(input_string)):
		return input_string;
	
	parser = StanfordParser()
	# Generates all possible parse trees sort by probability for the sentence
	possible_parse_tree_list = [tree for tree in parser.parse(input_string)]
	print("i am testing this",possible_parse_tree_list)
	# Get most probable parse tree
	parse_tree = possible_parse_tree_list[0]
	# print(parse_tree)
	# Convert into tree data structure
	parent_tree = ParentedTree.convert(parse_tree)
	
	modified_parse_tree = modify_tree_structure(parent_tree)
	
	parsed_sent = modified_parse_tree.leaves()
	return parsed_sent


# final word list
final_words= [];
# final word list that is detailed(dict)
final_words_detailed=[];


# pre processing text
def pre_process(text):
	remove_punct(word_list)
	final_words.extend(filter_words(word_list));
	lemmatize(final_words)


# checks if sigml file exists of the word if not use letters for the words
def final_output(input):
	final_string=""
	valid_words=open("words.txt",'r').read();
	valid_words=valid_words.split('\n')
	fin_words=[]
	for word in input:
		word=word.lower()
		if(word not in valid_words):
			for letter in word:
				# final_string+=" "+letter
				fin_words.append(letter);
		else:
			fin_words.append(word);

	return fin_words

final_output_in_sent=[];

# converts the final list of words in a final list with letters seperated if needed
def convert_to_final():
	for words in final_words:
		final_output_in_sent.append(final_output(words));



# takes input from the user
def take_input(text):
	test_input=text.strip().replace("\n","").replace("\t","")
	test_input2=""
	if(len(test_input)==1):
		test_input2=test_input;
	else:
		for word in test_input.split("."):
			test_input2+= word.capitalize()+" .";

	# pass the text through stanza
	some_text= en_nlp(test_input2);
	convert(some_text);


def convert(some_text):
	convert_to_sentence_list(some_text);
	convert_to_word_list(sent_list_detailed)

	# reorders the words in input
	for i,words in enumerate(word_list):
		word_list[i]=reorder_eng_to_isl(words)

	# removes punctuation and lemmatizes words
	pre_process(some_text);
	convert_to_final();
	remove_punct(final_output_in_sent)
	print_lists();
	

def print_lists():
	print("--------------------Word List------------------------");
	pprint.pprint(word_list)
	print("--------------------Final Words------------------------");
	pprint.pprint(final_words);
	print("---------------Final sentence with letters--------------")
	pprint.pprint(final_output_in_sent)

# clears all the list after completing the work
def clear_all():
	sent_list.clear();
	sent_list_detailed.clear();
	word_list.clear();
	word_list_detailed.clear();
	final_words.clear();
	final_words_detailed.clear();
	final_output_in_sent.clear();
	final_words_dict.clear();


# dict for sending data to front end in json
final_words_dict = {};

"""@app.route('/',methods=['GET'])
def index():
	clear_all();
	return render_template('index.html')"""


@app.route('/',methods=['GET','POST'])
def flask_test():
	clear_all();
	text = request.form.get('text') #gets the text data from input field of front end
	print("text is", text)
	if(text==""):
		return "";
	take_input(text)

	# fills the json 
	for words in final_output_in_sent:
		for i,word in enumerate(words,start=1):
			final_words_dict[i]=word;

	print("---------------Final words dict--------------");

	for key in final_words_dict.keys():
		if len(final_words_dict[key])==1:
			final_words_dict[key]=final_words_dict[key].upper()
	print(final_words_dict)

	print(final_words_dict)

	return final_words_dict;


# serve sigml files for animation
@app.route('/static/<path:path>')
def serve_signfiles(path):
	print("here");
	return send_from_directory('static',path)






if __name__=="__main__":
	# Open a tunnel to the web server
    app.run(host='127.0.0.1', port=3000)
