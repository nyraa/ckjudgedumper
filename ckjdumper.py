import requests
import json
import os
import sys
from markdownify import MarkdownConverter
import base64
import hashlib
import urllib.parse

sess = requests.Session()
sess.cookies.setdefault('connect.sid', sys.argv[1])

class ImageBlockConverter(MarkdownConverter):
    """
    Save base64 image to local
    """
    def convert_img(self, el, text, convert_as_inline):
        src = el.attrs.get('src', None) or ''
        alt = el.attrs.get('alt', None) or hashlib.md5(src.encode('utf-8')).hexdigest()
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

# homework, exam, misc
# type (hw, exam, misc)
#   chapter index
#   (chapter title, [problems title])
index_dicts = ({}, {}, {'misc': ('Problem without chapter', [])})
index_titles = ('Homeworks', 'Exams', 'Misc')

# TODO download chapters
res_homework = sess.get('https://ckj.imslab.org/homework')
homework = json.loads(res_homework.text)


# TODO foreach chapters
for chapter in homework['homework']:
    # TODO register index
    index_dicts[0][chapter['index']] = (chapter['title'], [])

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
    # TODO register index
    index_dicts[1][exam['index']] = (exam['title'], [])

    # TODO write exams info
    os.makedirs(exam['index'], exist_ok=True)
    with open(os.path.join(exam['index'], 'exam_raw.json'), 'w', encoding='utf-8') as exam_info:
        exam_info.write(json.dumps(exam, indent=4, ensure_ascii=False))


# TODO download problems
res_problems = sess.get('https://ckj.imslab.org/problems')
problems = json.loads(res_problems.text)


# TODO foreach problems
for problem in problems['problems']:
    # TODO register index
    chapter_index = problem['chapter']['index'] if problem['chapter'] else 'misc'
    for i in range(3):
        if chapter_index in index_dicts[i]:
            index_dicts[i][chapter_index][1].append(problem['title'])
            break

    # TODO download problem
    res_problem_info = sess.get(f'https://ckj.imslab.org/problems/{problem["id"]}')
    problem_info = json.loads(res_problem_info.text)
    del problem_info['totalRequest']
    del problem_info['acRequest']


    # TODO write problem info
    os.makedirs(os.path.join(chapter_index, problem['title']), exist_ok=True)
    os.chdir(os.path.join(chapter_index, problem['title']))
    with open('problem_raw.json', 'w', encoding='utf-8') as prob_info:
        prob_info.write(json.dumps(problem_info, indent=4, ensure_ascii=False))
    # MD
    with open('README.md', 'w', encoding='utf-8') as readme_md:
        readme_md.write(f"""\
## {problem_info["title"]}
<details>
<summary>Details</summary>

Level: {problem['level']}  
Tags: {', '.join(problem_info['tags'])}  
Problem ID: [{problem['id']}](https://ckj.imslab.org/#/problems/{problem['id']})  
</details>

### Description
{md(problem_info['description'])}
### Input
{problem_info['inputFormat'] if problem_info['inputFormat'] else 'No input'}
### Output
{problem_info['outputFormat']}
""")

        if problem_info['loaderCode']:
            loader_code = problem_info['loaderCode'].replace('\r', '')
            readme_md.write(f"""
### Loader Code
<details>
<summary>Loader Code</summary>

```c
{loader_code}
```
</details>

""")
        for i, sample in enumerate(problem_info['samples']):
            readme_md.write(f"""
### Example {i + 1}
#### Input
```
{sample['inputData']}
```
#### Output
```
{sample['outputData']}
```
""")
        readme_md.write(f"""
### Limits
Your program needs to finish task in {problem_info['timeLimit']} seconds.  
Your program can only use memory less than {problem_info['memLimit']} KB.  
""")
        if problem_info['hint']:
            readme_md.write(f"""
### Hint
<details>
<summary>Hint</summary>
{problem_info['hint']}
</details>
""")

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
        submission_f.write(res_submission.text.replace('\t', '    '))
    os.chdir(os.path.join('..', '..'))

# TODO write global index
with open('README.md', 'w', encoding='utf-8') as index:
    for i in range(3):
        index.write(f'- {index_titles[i]}\n')
        for chapter in index_dicts[i]:
            index.write(f'  - [{chapter} - {index_dicts[i][chapter][0]}](/{chapter})\n')
            fo = open(os.path.join(chapter, 'README.md'), 'w', encoding='utf-8')
            fo.write(f'# {chapter}\n')
            for problem_title in index_dicts[i][chapter][1]:
                index.write(f'    - [{problem_title}](/{urllib.parse.quote(f"{chapter}/{problem_title}")})\n')
                with open(os.path.join(chapter, problem_title, 'README.md'), encoding='utf-8') as fi:
                    fo.writelines(fi.readlines())
            fo.close()