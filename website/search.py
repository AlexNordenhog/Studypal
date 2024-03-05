import difflib
from db.database import d

class SearchError(Exception):
    pass

class Search:
    def search(self, query, university=None, subject=None, course=None):
        '''
        Search function to search for courses in the database.
        
        Parameters:
        - query: Search keyword provided by the user. Can be empty, meaning no keyword search.
        - university: Selected university.
        - subject: Selected subject.
        - course: Selected course.

        Returns a list of matching courses based on the search criteria.
        '''
        try:
            filtered_courses = []

            if university and subject and course:
                subject_courses = d.get_courses_from_subject_at_university(university, subject)
                for c in subject_courses:
                    if c == course:
                        filtered_courses.append(c)

            elif university and subject and not course:
                subject_courses = d.get_courses_from_subject_at_university(university, subject)
                filtered_courses.extend(subject_courses)

            elif university and not subject and not course:
                university_courses = d.get_courses_from_university(university)
                filtered_courses.extend(university_courses)

            elif not university and subject and not course:
                subject_courses = d.get_courses_from_subject(subject)
                filtered_courses.extend(subject_courses)

            elif not university and not subject and not course:
                all_courses = d.get_all_courses()
                filtered_courses.extend(all_courses)

            matching_courses = []
            if query:
                lower_filtered_courses = [c.lower() for c in filtered_courses]
                n_matches = max(1, len(filtered_courses))
                if filtered_courses:
                    close_matches = difflib.get_close_matches(query.lower(), lower_filtered_courses, n=n_matches, cutoff=0.5)
                    matching_courses = [filtered_courses[lower_filtered_courses.index(match)] for match in close_matches]
                else:
                    all_courses = d.get_all_courses()
                    lower_courses = [item.lower() for item in all_courses]
                    close_matches = difflib.get_close_matches(query.lower(), lower_courses, n=n_matches, cutoff=0.5)
                    upper_close_matches = [item.upper() for item in close_matches]
                    matching_courses = upper_close_matches

            else:
                matching_courses = filtered_courses

            return matching_courses
        except:
            raise SearchError()

s = Search()