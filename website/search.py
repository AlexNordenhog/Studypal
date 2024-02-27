import difflib
from db.database import d

def search(query, university=None, subject=None, course=None):
    '''
    Search function to search for courses in the database.
    
    Parameters:
    - query: Search keyword provided by the user. Can be empty, meaning no keyword search.
    - university: Selected university.
    - subject: Selected subject.
    - course: Selected course.

    Returns a list of matching courses based on the search criteria.
    '''
    filtered_courses = []

    if university and subject and course:
        print(1)
        print(course)
        courses = d._get_keys(str('documents/' + university + '/' + subject))
        for c in courses:
            if c == course:
                filtered_courses.append(c)

    elif university and subject and not course:
        print(2)
        courses = d._get_keys(str('documents/' + university + '/' + subject))
        filtered_courses.extend(courses)

    elif university and not subject and not course:
        print(3)
        subjects = d._get_keys(str('documents/' + university))
        for subject in subjects:
            courses = d._get_keys(str('documents/' + university + '/' + subject))
            filtered_courses.extend(courses)

    elif not university and subject and not course:
        print(4)
        universities = d._get_keys('documents')
        for university in universities:
            subjects = d._get_keys(str('documents/' + university))
            for s in subjects:
                if s == subject:
                    courses = d._get_keys(str('documents/' + university + '/' + s))
                    filtered_courses.extend(courses)
    else:
        print(5)

    matching_courses = []
    if query:
        lower_filtered_courses = [c.lower() for c in filtered_courses]
        n_matches = max(1, len(filtered_courses))
        print(6)
        if filtered_courses:
            print(7)
            close_matches = difflib.get_close_matches(query.lower(), lower_filtered_courses, n=n_matches, cutoff=0.5)
            matching_courses = [filtered_courses[lower_filtered_courses.index(match)] for match in close_matches]
        else:
            print(8)
            all_courses = []
            universities = d._get_keys('documents')
            for university in universities:
                subjects = d._get_keys(str('documents/' + university))
                for s in subjects:
                    all_courses.extend(d._get_keys(str('documents/' + university + '/' + s)))
            lower_courses = [item.lower() for item in all_courses]
            close_matches = difflib.get_close_matches(query.lower(), lower_courses, n=n_matches, cutoff=0.5)
            upper_close_matches = [item.upper() for item in close_matches]
            matching_courses = upper_close_matches

    else:
        print(9)
        matching_courses = filtered_courses

    return matching_courses
