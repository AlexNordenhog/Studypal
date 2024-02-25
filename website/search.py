import difflib

def search(university_data, query, university=None, subject=None, course=None):
    '''
    Filters university_data based on university, subject, and course selections, and then
    performs a keyword search within that filtered list if a query is provided.
    
    Parameters:
    - university_data: A nested dictionary with structure {'University': {'Subject': ['Course', ...]}}
    - query: Search keyword provided by the user. Can be empty, meaning no keyword search.
    - university: Selected university.
    - subject: Selected subject.
    - course: Selected course.

    Returns a list of matching courses based on the search criteria.
    '''
    filtered_courses = []

    if university in university_data:
        uni_data = university_data[university]
        if subject in uni_data:
            subj_data = uni_data[subject]
            if course in subj_data:
                filtered_courses = [c for c in subj_data if course.lower() in c.lower()]
            else:
                filtered_courses = subj_data
        else:
            for subj_courses in uni_data.values():
                filtered_courses.extend(subj_courses)
    else:
        for uni_subjects in university_data.values():
            for subj_courses in uni_subjects.values():
                filtered_courses.extend(subj_courses)

    matching_courses = []
    if query:
        lower_filtered_courses = [c.lower() for c in filtered_courses]
        n_matches = max(1, len(filtered_courses))
        close_matches = difflib.get_close_matches(query.lower(), lower_filtered_courses, n=n_matches, cutoff=0.5)
        matching_courses = [filtered_courses[lower_filtered_courses.index(match)] for match in close_matches]
    else:
        matching_courses = filtered_courses

    return matching_courses
