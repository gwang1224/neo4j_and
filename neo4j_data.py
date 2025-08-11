import openAlex_to_HGCN as oth

author_name = "David Nathan"

#1. Fetch author data from OpenAlex
author_data = oth.fetch_author_data(author_name)

#2. Mapping author ID to lable (0,1,2,...)
author_id_to_label = {}
for i, author_id in enumerate(author_data.keys()):
    author_id_to_label[author_id] = str(i)

#3. Fetch works for each author
works_data = {}
for author_id, author in author_data.items():
    author_works = oth.fetch_works_for_author(author_id)
    author["works"] = [w["id"] for w in author_works]

    for work in author_works:
            works_data[work["id"]] = work

#4. Save to JSON
oth.save_data_to_json(author_name, author_data, works_data, author_id_to_label)


