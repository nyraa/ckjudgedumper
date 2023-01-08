import requests
import json
import os
import sys

sess = requests.Session()
sess.cookies.setdefault('connect.sid', sys.argv[0])

os.makedirs('dump', exist_ok=True)
os.chdir('dump')

# TODO download chapters
res_homework = sess.get('https://ckj.imslab.org/homework')
homework = json.loads(res_homework.text)
# TODO foreach chapters
for chapter in homework['homework']:
    # TODO write chapter info
    os.makedirs(chapter['index'], exist_ok=True)
    with open(os.path.join(chapter['index'], 'chapter_raw.json'), 'w', encoding='utf-8') as ch_info:
        ch_info.write(json.dumps(chapter, indent=2, ensure_ascii=False))
# TODO download exams
# TODO foreach exams
    # TODO write exams info
# TODO download problems
# TODO foreach problems
    # TODO download problem
    # TODO write problem info
    # TODO download submission
    # TODO write submission