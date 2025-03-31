import streamlit as st
import nltk
import spacy
nltk.download('stopwords')
spacy.load('en_core_web_sm')
import pandas as pd
from pathlib import Path
import time, datetime
import base64, random
from pdfminer3.layout import LAParams
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfpage import PDFPage
from pdfminer3.converter import TextConverter
from pdfminer3.pdfinterp import PDFPageInterpreter
from streamlit_tags import st_tags
from PIL import Image
import io, random
import pymysql
from courses import job_courses
import plotly.express as px
import PyPDF2
import joblib
import Skills
import yt_dlp
from ResumeParser import EnhancedResumeParser
# from resume_parser import resumeparse


knn = joblib.load('knn_model.joblib')
tfidf = joblib.load('tfidf_vectorizer.joblib')

#identify the job
def predict_job_profile(pdf_file_path):
  """
  Predicts the job profile for a new resume in PDF format.

  Args:
    pdf_file_path: Path to the PDF file containing the resume.

  Returns:
    str: The predicted job profile.
  """
  try:
    # Extract text from the PDF
    with open(pdf_file_path, 'rb') as fileobj:
      pdf_reader = PyPDF2.PdfReader(fileobj)
      text = ""
      for page in pdf_reader.pages:
        text += page.extract_text()

    # Preprocess the text
    new_resume = tfidf.transform([text])

    # Make prediction
    prediction = knn.predict(new_resume)

    return prediction[0]
  except Exception as e:
    print(f"An error occurred: {e}")
    return "Unable to predict job profile."
#import youtube_dlrpr
def fetch_yt_video(link):
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(link, download=False)
        video_title = info_dict.get('title', None)
    return video_title
def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in: dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode() # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
            text = fake_file_handle.getvalue()
    # close open handles
    converter.close()
    fake_file_handle.close()
    return text
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"type="application/pdf">
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 4, 2)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break   
    return rec_course
connection = pymysql.connect(host='localhost', user='root', password='root')
cursor = connection.cursor()
def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills,recommended_skills,courses):
    try:
        connection = pymysql.connect(
            host='localhost',
            database='sra',
            user='root',
            password='root'
        )
        if connection:
            cursor = connection.cursor()
            insert_query = """
            INSERT INTO user_data (name, email_id, resume_score, timestamp, Page_no, Predicted_Field, User_level, Actual_skills, Recommended_skills, Recommended_courses)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            record = (name, email,res_score, timestamp, no_of_pages,reco_field, cand_level, skills, recommended_skills,courses)
            cursor.execute(insert_query, record)
            connection.commit()
            cursor.close()
            connection.close()
    except pymysql.Error as e:
        st.error(f"Error: {e}")
    # st.set_page_config(
    # page_title="Smart Resume Analyzer",
    # page_icon='./Logo/SRA_Logo.ico',
    # )
def run():
    st.title("AI Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    # link = '[©Developed by Spidy20](http://github.com/spidy20)'
    # st.sidebar.markdown(link, unsafe_allow_html=True)
    img = Image.open('./Logo/SRA_Logo.jpg')
    img = img.resize((250, 250))
    st.image(img)
    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)
    connection.select_db("sra")
    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
    (ID INT NOT NULL AUTO_INCREMENT,
    Name varchar(100) NOT NULL,
    Email_ID VARCHAR(50) NOT NULL,
    resume_score VARCHAR(8) NOT NULL,
    Timestamp VARCHAR(50) NOT NULL,
    Page_no VARCHAR(5) NOT NULL,
    Predicted_Field VARCHAR(25) NOT NULL,
    User_level VARCHAR(30) NOT NULL,
    Actual_skills VARCHAR(300) NOT NULL,
    Recommended_skills VARCHAR(300) NOT NULL,
    Recommended_courses VARCHAR(600) NOT NULL,
    PRIMARY KEY (ID));
    """
    cursor.execute(table_sql)
    
    if choice == 'Normal User':
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smartrecommendation based on it."</h4>''',
        # unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            # with st.spinner('Uploading your Resume....'):
            # time.sleep(4)
            
            save_image_path ='./Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resumeparser = EnhancedResumeParser()
            resume_data = resumeparser.parse_resume(save_image_path)
            # resume_data = ResumeParser(save_image_path).get_extracted_data()
            # resume_data2 = resumeparse.read_file(save_image_path)
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)
                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['personal_info']['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' +  resume_data['personal_info']['name'])
                    st.text('Email: ' +  resume_data['personal_info']['email'])
                    st.text('Contact: ' +  resume_data['personal_info']['contact'])
                    st.text('Resume pages: ' + str(resume_data['metadata']['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if  resume_data['metadata']['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are at looking Fresher.</h4>''', unsafe_allow_html=True)
                elif  resume_data['metadata']['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''', unsafe_allow_html=True)
                elif  resume_data['metadata']['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!</h4>''', unsafe_allow_html=True)
               
                st.subheader("**Skills Recommendation **")
                ## Skill shows
                keywords = st_tags(label='### Skills that you have', text='See our skills recommendation', value=resume_data['skills'], key='1')
                ## recommendation
                profile = predict_job_profile(save_image_path)
                recommended_skills = []
                reco_profile = profile
                rec_course = ''
                ## Courses recommendation
                
                st.success('''** According to our Analysis the Job profile you are suitable for is {} **'''.format(profile))
                job_description = Skills.job_profiles[profile]['description']
                st.markdown("""<h4> Description:<br> {} </h4>""".format(job_description),unsafe_allow_html=True)
                recommended_skills = Skills.job_profiles[profile]['skills']
                st_tags(label='### Recommended skills for you.', text='Recommended skills generated from System', value=recommended_skills, key='2')
                st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job </h4>''', unsafe_allow_html=True)
                rec_course = course_recommender(job_courses[str(profile)])
            
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas **")
                resume_score = 0

                if 'objective' in resume_text.lower():
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added
                        Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add
                        your career objective, it will give your career intention to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if 'declaration' in resume_text.lower():
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added
                        Declaration✍</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add
                        Declaration✍. It will give the assurance that everything written on your resume is true and fully
                        acknowledged by you</h4>''',
                        unsafe_allow_html=True)

                if 'hobbies' in resume_text.lower() or 'interests' in resume_text.lower():
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your
                        Hobbies </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add
                        Hobbies. It will show your personality to the Recruiters and give the assurance that you are fit for this role
                        or not.</h4>''',
                        unsafe_allow_html=True)

                if 'achievements' in resume_text.lower():
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your
                        Achievements </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add
                        Achievements. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'projects' in resume_text.lower():
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your
                        Projects </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add
                        Projects. It will show that you have done work related to the required position or not.</h4>''',
                        unsafe_allow_html=True)

                st.subheader("**Resume Score **")
                st.markdown(
                    """
                    <style>
                    .stProgress > div > div > div > div {
                    background-color: #d73b5c;
                    }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)

                st.success('** Your Resume Writing Score: ' + str(score) + '**')
                st.warning("** Note: This score is calculated based on the content that you have added in your Resume.**")
                st.balloons()
                insert_data( resume_data['personal_info']['name'],  resume_data['personal_info']['email'], str(resume_score), timestamp,
                            str(resume_data['metadata']['no_of_pages']), reco_profile, cand_level, str(resume_data['skills']),
                            str(recommended_skills), str(rec_course))

                ## Resume writing video
                st.header("**Bonus Video for Resume Writing Tips **")
                resume_vid = random.choice(job_courses['resume'])
                res_vid_title = fetch_yt_video(resume_vid)
                st.subheader(" **" + res_vid_title + "**")
                st.video(resume_vid)

                ## Interview Preparation Video
                st.header("**Bonus Video for Interview Tips **")
                interview_vid = random.choice(job_courses['interview prep'])
                int_vid_title = fetch_yt_video(interview_vid)
                st.subheader(" **" + int_vid_title + "**")
                st.video(interview_vid)

                connection.commit()
            else:
                st.error("something went wrong")
        else:
            pass
    else:
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'machine_learning_hub' and ad_password == 'mlhub123':
                st.success("Welcome Kushal")
                # Display Data
                cursor.execute('''SELECT * FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'),
                            unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)
                ## Pie chart for predicted field recommendations
                predicted_field_counts = df['Predicted Field'].value_counts().reset_index()
                predicted_field_counts.columns = ['Predicted Field', 'Count']
                st.subheader(" **Pie-Chart for Predicted Field Recommendations**  ")
                fig = px.pie(predicted_field_counts, values='Count', names='Predicted Field', 
                            title='Predicted Field according to the Skills')
                st.plotly_chart(fig)
                ### Pie chart for User's Experienced Level
                labels = df['User Level'].value_counts().reset_index()
                labels.columns = ['user Experience','count']
                st.subheader(" ** Pie-Chart for User's Experienced Level**")
                fig = px.pie(labels, values='count', names='user Experience', title="Pie-Chart for User's Experienced Level")
                st.plotly_chart(fig)
            else:
                st.error("Wrong ID & Password Provided")
run()

