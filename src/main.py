import collections
import hashlib
import os
import random
import sys
import xml.etree.ElementTree as ET


class Section:
    def __init__(self, name):
        self.name = name
        self.questions = []

    def merge(self, other):
        self.questions += other.questions

    def addQuestion(self, question):
        assert question not in self.questions
        self.questions.append(question)

    def shuffle(self):
        for question in sorted(self.questions, key=lambda o: o.text):
            question.shuffle()

        random.shuffle(self.questions)

    def reduceQuestionsToSample(self, k):
        self.questions = random.sample(self.questions, k)

    def toLaTeX(self):
        # latex = 'section'
        latex = ''
        for question in self.questions:
            latex += '\n'
            latex += question.toLaTeX()
        latex += '\n'
        return latex

    @classmethod
    def fromXmlElement(cls, element):
        assert element.tag == 'section'

        name = element.get('name')
        assert name is not None

        section = Section(name)
        for element in element.findall('question'):
            question = Question.fromXmlElement(element)
            section.addQuestion(question)

        return section


class Question:
    def __init__(self, text, answers):
        self.text = text
        self.answers = answers

    def shuffle(self):
        self.answers.shuffle()

    def __eq__(self, other):
        if isinstance(other, Question):
            return self.text == other.text and self.answers == other.answers
        else:
            return False

    def toLaTeX(self):
        latex = '\\question'
        latex += '\n'
        latex += self.text
        latex += '\n'
        latex += self.answers.toLaTeX()
        latex += '\n'
        return latex

    @classmethod
    def fromXmlElement(cls, element):
        text_element = element.find('text')
        assert text_element is not None
        text = text_element.text.strip()

        answers_element = element.find('answers')
        answers = Answers.fromXmlElement(answers_element)

        return Question(text, answers)


class Answers:
    def __init__(self):
        self.groups = []

    def __eq__(self, other):
        if isinstance(other, Answers):
            return self.groups == other.groups
        else:
            return False

    def shuffle(self):
        for group in self.groups:
            group.shuffle()

    def toLaTeX(self):
        latex = ''
        for group in self.groups:
            latex += '\n'
            latex += group.toLaTeX()
        latex += '\n'
        return latex

    @classmethod
    def fromXmlElement(cls, answers_element):
        answers = Answers()

        for group_element in answers_element:
            group = AnswersGroup.fromXmlElement(group_element)
            answers.groups.append(group)

        return answers


class AnswersGroup:
    supported_group_types = ['fill-blank', 'choose-multiple', 'choose-single']

    def __init__(self, type):
        self.type = type
        self.choices = []

    def shuffle(self):
        random.shuffle(self.choices)

    def __eq__(self, other):
        if isinstance(other, AnswersGroup):
            return self.type == other.type and self.choices == other.choices
        else:
            return False

    def toLaTeX(self):
        is_blank = self.type != 'fill-blank'
        if is_blank:
            latex = '\\begin{choices}'
            latex += '\n'
        else:
            latex = ''

        for choice in self.choices:
            latex += '\n'
            latex += choice.toLaTeX()
        if is_blank:
            latex += '\n'
            latex += '\\end{choices}'
        latex += '\n'
        return latex

    @classmethod
    def fromXmlElement(cls, group_element):
        tag = group_element.tag
        assert tag in cls.supported_group_types
        group = AnswersGroup(tag)

        if group.type == 'fill-blank':
            choice = BlankChoice.fromXmlElement(group_element)
            group.choices.append(choice)
        else:
            for choice_element in group_element:
                choice = Choice.fromXmlElement(choice_element)
                group.choices.append(choice)

        return group


class BlankChoice:
    def __init__(self, correct_answer, length_inches):
        self.correctAnswer = correct_answer
        self.length = length_inches

    def toLaTeX(self):
        latex = '\\fillin'
        if self.correctAnswer is not None:
            latex += '[' + self.correctAnswer + ']'
        latex += '[' + self.length + 'in]'
        return latex

    def __eq__(self, other):
        if isinstance(other, BlankChoice):
            return self.correctAnswer == other.correctAnswer
        else:
            return False

    @classmethod
    def fromXmlElement(cls, element):
        correct_text_element = element.find('correct-text')
        text = None
        if correct_text_element is not None:
            text = correct_text_element.text.strip()

        length = element.get('length', '2')

        return BlankChoice(text, length)


class Choice:
    supported_choice_types = ['correct-choice', 'choice']

    def __init__(self, is_correct, text):
        self.is_correct = is_correct
        self.text = text

    def __eq__(self, other):
        if isinstance(other, Choice):
            return self.is_correct == other.is_correct and self.text == other.text
        else:
            return False

    def toLaTeX(self):
        if self.is_correct:
            latex = '\\CorrectChoice'
        else:
            latex = '\\choice'

        latex += ' ' + self.text
        latex += '\n'
        return latex

    @classmethod
    def fromXmlElement(cls, element):
        tag = element.tag
        assert tag in cls.supported_choice_types
        is_correct = (tag == 'correct-choice')
        text = element.text.strip()

        return Choice(is_correct, text)


class Exam:
    def __init__(self, seed, title, name, variant, showCorrectAnswers):
        self.seed = seed
        self.title = title
        self.name = name
        self.variant = variant
        self.showCorrectAnswers = showCorrectAnswers
        self.sections = collections.OrderedDict()

    def addOrMergeSection(self, section):
        if self.sectionExists(section):
            self.mergeSection(section)
        else:
            self.addSection(section)

    def mergeSection(self, section):
        assert self.sectionExists(section)
        self.sections[section.name].merge(section)

    def addSection(self, section):
        self.sections[section.name] = section

    def sectionExists(self, section):
        return section.name in self.sections

    def sectionExistsByName(self, name):
        return name in self.sections

    def processFile(self, filename):
        tree = ET.parse(filename)
        section_element = tree.getroot()
        section = Section.fromXmlElement(section_element)
        self.addOrMergeSection(section)

    def shuffle(self):
        for section in sorted(self.sections.values(), key=lambda o: o.name):
            section.shuffle()

    def print(self):
        for blah in sorted(self.__dict__.items(), key=lambda o:o[0]):
            print(blah)

    def toLaTeX(self):
        latex = """
        \\documentclass[a4paper""" + (',answers' if self.showCorrectAnswers else '') + """]{exam}

        \\usepackage[T2A]{fontenc}
        \\usepackage[utf8]{inputenc}
        \\usepackage[bulgarian]{babel}
        \\selectlanguage{bulgarian}
        \\usepackage{minted}

        \\usepackage{color}

        \\pagestyle{headandfoot}

        \\runningheadrule
        \\runningfootrule

        \\firstpageheadrule
        \\firstpagefootrule

        \\firstpageheader{""" + self.name + """}{""" + self.title + """}{""" + self.variant + ' ' + str(self.seed) + """}
        \\runningheader{""" + self.name + """}{""" + self.title + """}{""" + self.variant + ' ' + str(self.seed) + """}

        \\firstpagefooter{}{\\thepage\\ / \\numpages}{}
        \\runningfooter{}{\\thepage\\ / \\numpages}{}


        \\begin{document}

        \\begin{questions}

        """

        for section in self.sections.values():
            latex += '\n'
            latex += section.toLaTeX()

        latex += """

        \\end{questions}
        \\end{document}
        """

        return latex

    @classmethod
    def fromConfig(cls, config):

        def helper(seed, title, name, variant, showCorrectAnswers, files, questionsPerSection):
            random.seed(seed)

            exam = Exam(seed, title, name, variant, showCorrectAnswers)
            for filename in files:
                exam.processFile(filename)

            exam.shuffle()

            for section_name, num_questions in questionsPerSection.items():
                assert exam.sectionExistsByName(section_name)
                section = exam.sections[section_name]
                section.reduceQuestionsToSample(num_questions)

            return exam

        exams = []
        for seed in sorted(config.seeds):
            args = {
                'seed': seed,
                'title': config.title,
                'name': config.name,
                'variant': config.variant,
                'showCorrectAnswers': False,
                'files': config.files,
                'questionsPerSection': config.questionsPerSection
            }

            exam = helper(**args)
            exams.append(exam)

            if config.correctAnswersVariant:
                args['showCorrectAnswers'] = True
                exam = helper(**args)
                exams.append(exam)

        return exams


class Configuration:
    def __init__(self, seeds):
        self.seeds = seeds
        self.files = []
        self.title = 'Physics'
        self.name = 'Exam'
        self.variant = 'var'
        self.correctAnswersVariant = True
        self.questionsPerSection = collections.OrderedDict()

    @classmethod
    def fromXmlFile(cls, filename):
        assert os.path.isfile(filename)

        tree = ET.parse(filename)
        config_element = tree.getroot()

        seeds_element = config_element.find('seeds')
        assert seeds_element is not None

        seeds = []
        for seed_element in seeds_element:
            seed = int(seed_element.text.strip())
            assert seed is not None
            seeds.append(seed)
        assert len(seeds) > 0

        config = Configuration(seeds)

        files_element = config_element.find('files')
        assert files_element is not None

        config_dirname = os.path.dirname(filename)
        for file_element in files_element:
            # resolve files relative to config directory
            filename = os.path.join(config_dirname, file_element.text.strip())
            assert os.path.isfile(filename)
            config.files.append(filename)

        sections_element = config_element.find('sections')
        assert sections_element is not None

        for section_element in sections_element:
            name = section_element.get('name').strip()
            questions_element = section_element.find('questions')
            assert questions_element is not None
            config.questionsPerSection[name] = int(questions_element.text.strip())

        title_element = config_element.find('title')
        if title_element is not None:
            config.title = title_element.text.strip()

        name_element = config_element.find('name')
        if name_element is not None:
            config.name = name_element.text.strip()

        variant_element = config_element.find('variant')
        if variant_element is not None:
            config.variant = variant_element.text.strip()

        correct_answers_variant_element = config_element.find('correct-answers-variant')
        if correct_answers_variant_element is not None:
            if correct_answers_variant_element.text is not None:
                config.correctAnswersVariant = bool(correct_answers_variant_element.text.strip())
            else:
                config.correctAnswersVariant = False

        return config


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] + " CONFIG_FILE")
        sys.exit(1)

    config = Configuration.fromXmlFile(sys.argv[1])
    exams = Exam.fromConfig(config)
    for exam in sorted(exams, key=lambda f: f.seed):
        print(exam.seed)
        with open('exam_' + str(exam.seed) + ('_answers' if exam.showCorrectAnswers else '') + '.tex', 'w') as f:
            print(exam.toLaTeX(), file=f)
        m = hashlib.sha512()
        exam.print()
        m.update(bytes(exam.toLaTeX(), encoding="utf8"))
        print(m.hexdigest())
