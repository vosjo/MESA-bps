 
#Load the packages
import os
import pandas as pd
from flask import Flask, flash, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

import urllib


#added try catch to allow local running of the code without heroku
try:
    from MESAbps import predictions
except:
    import predictions
    
UPLOAD_FOLDER = os.path.join('MESAbps','uploads')
DOWNLOAD_FOLDER = os.path.join('MESAbps','downloads')
ALLOWED_EXTENSIONS = {'txt', 'csv'}

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
if not os.path.isdir(DOWNLOAD_FOLDER):
    os.mkdir(DOWNLOAD_FOLDER)

#Connect the app
app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def arguments2float(*args):

    results = []

    for arg in args:
        if arg == '':
            results.append(None)
        else:
            results.append(float(arg))

    return results

@app.route('/upload/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('homepage'))
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('homepage'))
        
        if file and not allowed_file(file.filename):
            flash('File type not allowed, try .txt or .csv')
            return redirect(url_for('homepage'))
        
        elif file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the input file
            try:
                df = pd.read_csv(filepath)
                os.remove(filepath)
            except Exception:
                flash('Can not read file')
                os.remove(filepath)
                return redirect(url_for('homepage'))
            
            if not predictions.correct_input_pars(df):
                flash('File does not contain the correct parameters: {}'.format(predictions.NECESSARY_PARAMETERS) )
                return redirect(url_for('homepage'))
            
            results = predictions.predict(df)
            results.to_csv(app.config['DOWNLOAD_FOLDER'] + '/' + filename)
            
            return redirect(url_for('download_and_remove',
                                    filename=filename))
        
    return redirect(url_for('homepage'))
    
@app.route('/downloads/<filename>')
def download_results(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'],
                               filename)

@app.route('/download_and_remove/<filename>')
def download_and_remove(filename):
    path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)

    def generate():
        with open(path) as f:
            yield from f

        os.remove(path)

    r = app.response_class(generate(), mimetype='text/csv')
    r.headers.set('Content-Disposition', 'attachment', filename='bps_results.csv')
    return r


@app.route('/')
def homepage():

    M1init = request.args.get('M1init', '')
    M2init = request.args.get('M2init', '')
    qinit = request.args.get('qinit', '')
    Pinit = request.args.get('Pinit', '')
    FeHinit = request.args.get('FeHinit', '')

    M1init, M2init, qinit, Pinit, FeHinit = arguments2float(M1init, M2init, qinit, Pinit, FeHinit)

    if qinit is None and M1init is not None and M2init is not None:
        qinit = M1init / M2init

    render_kws = {}
    
    if M1init is not None and qinit is not None and Pinit is not None and FeHinit is not None:
        df = pd.DataFrame(data=[[M1init, qinit, Pinit, FeHinit]], 
                          columns=['M1_init', 'q_init', 'P_init', 'FeH_init'])
        
        results = predictions.predict(df)
        
        render_kws['results'] = results.to_html()

    # Render the page
    return render_template('home.html', **render_kws)


if __name__ == '__main__':
    app.run(debug=True, threaded=True) # Set to false when deploying
