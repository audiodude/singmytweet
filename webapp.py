import os

from create_song import text_to_song_file

from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/sing', methods=['GET', 'POST'])
def sing_text():
    if request.method == 'POST':
        song_file = text_to_song_file(request.form['text'])
        base = os.path.basename(song_file)
        new_path = os.path.join(os.path.abspath('.'), 'static', base)
        os.rename(song_file, new_path)
        return render_template('sing.html', song='/static/%s' % base)
    else:
        return render_template('sing.html', song=None)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
