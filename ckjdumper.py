import requests
import json
import os
import sys
import markdownify
from markdownify import MarkdownConverter
import base64

sess = requests.Session()
sess.cookies.setdefault('connect.sid', sys.argv[1])

class ImageBlockConverter(MarkdownConverter):
    """
    Save base64 image to local
    """
    def convert_img(self, el, text, convert_as_inline):
        src = el.attrs.get('src', None) or ''
        alt = el.attrs.get('alt', None) or str(hash(src))
        if src.startswith('data:'):
            img_data = src.split(',')[1]
            os.makedirs('img', exist_ok=True)
            with open(os.path.join('img', alt), 'wb') as img:
                img.write(base64.decodebytes(bytes(img_data, encoding='utf-8')))
            el.attrs['src'] = f'img/{alt}'
        return super().convert_img(el, text, convert_as_inline) + '\n\n'
def md(html, **options):
    return ImageBlockConverter(**options).convert(html)
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
        ch_info.write(json.dumps(chapter, indent=4, ensure_ascii=False))


# TODO download exams
res_exams = sess.get('https://ckj.imslab.org/exams')
exams = json.loads(res_exams.text)
'''
with open('../exam.json', encoding='utf-8') as exam_f:
    exams = json.load(exam_f)
'''


# TODO foreach exams
for exam in exams['exams']:
    # TODO write exams info
    os.makedirs(exam['index'], exist_ok=True)
    with open(os.path.join(exam['index'], 'exam_raw.json'), 'w', encoding='utf-8') as exam_info:
        exam_info.write(json.dumps(exam, indent=4, ensure_ascii=False))


# TODO download problems
res_problems = sess.get('https://ckj.imslab.org/problems')
problems = json.loads(res_problems.text)


# TODO foreach problems
for problem in problems['problems']:
    # TODO download problem
    res_problem_info = sess.get(f'https://ckj.imslab.org/problems/{problem["id"]}')
    problem_info = json.loads(res_problem_info.text)
    del problem_info['totalRequest']
    del problem_info['acRequest']
    ch_dirname = problem['chapter']['index'] if problem['chapter'] else 'misc'


    # TODO write problem info
    os.makedirs(os.path.join(ch_dirname, problem['title']), exist_ok=True)
    os.chdir(os.path.join(ch_dirname, problem['title']))
    with open('problem_raw.json', 'w', encoding='utf-8') as prob_info:
        prob_info.write(json.dumps(problem_info, indent=4, ensure_ascii=False))
    # MD
    with open('README.md', 'w', encoding='utf-8') as readme_md:
        readme_md.write(f'# {problem_info["title"]}\n')
        readme_md.write('### Tags\n')
        readme_md.write('\n'.join(['* ' + x for x in problem_info['tags']]) + '\n')
        readme_md.write('### Description\n')
        readme_md.write(md(problem_info['description']))

    # TODO download submission
    res_submissions_info = sess.get(f'https://ckj.imslab.org/user/submission/{problem["id"]}')
    if res_submissions_info.status_code == 404:
        os.chdir(os.path.join('..', '..'))
        continue
    submissions_info = json.loads(res_submissions_info.text)
    if not submissions_info['submissionInfo'][-1]['status'] == 'Accepted':
        os.chdir(os.path.join('..', '..'))
        continue
    res_submission = sess.get(f'https://ckj.imslab.org/user/code/{submissions_info["submissionInfo"][-1]["submissionId"]}')


    # TODO write submission
    with open('submission.c', 'w', encoding='utf-8') as submission_f:
        submission_f.write(res_submission.text)
    os.chdir(os.path.join('..', '..'))