"""
    Copyright (c) 2015 Raj Patel(raj454raj@gmail.com), StopStalk

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
"""

import re
import utilities
import profilesites as profile

# ----------------------------------------------------------------------------
def pie_chart_helper():
    """
        Helper function for populating pie chart with different
        submission status of a problem
    """

    problem_name = request.post_vars["pname"]
    stable = db.submission
    count = stable.id.count()
    row = db(stable.problem_name == problem_name).select(stable.status,
                                                         count,
                                                         groupby=stable.status)
    return dict(row=row)

# ----------------------------------------------------------------------------
def urltosite(url):
    """
        Helper function to extract site from url
    """

    # Note: try/except is not added because this function is not to
    #       be called for invalid problem urls
    site = re.search("www.*com", url).group()

    # Remove www. and .com from the url to get the site
    site = site[4:-4]

    return site

# ----------------------------------------------------------------------------
def index():
    """
        The main problem page
    """

    if request.vars.has_key("pname") == False or \
        request.vars.has_key("plink") == False:

        # Disables direct entering of a URL
        session.flash = "Please click on a Problem Link"
        redirect(URL("default", "index"))

    stable = db.submission
    problem_name = request.vars["pname"]
    problem_link = request.vars["plink"]

    submissions = db(stable.problem_link == problem_link).select(orderby=~stable.time_stamp)
    site = urltosite(problem_link)
    try:
        tags_func = getattr(profile, site + "_get_tags")
        all_tags = tags_func(problem_link)
        if all_tags != []:
            tags = DIV(_class="center")
            for tag in all_tags:
                tags.append(DIV(A(tag,
                                  _href=URL("problems",
                                            "tag",
                                            vars={"q": tag}),
                                  _style="color: white;"),
                            _class="chip"))
                tags.append(" ")
        else:
            tags = DIV("No tags available")
    except AttributeError:
        tags = DIV("No tags available")

    problem_details = TABLE(_style="float: left; width: 30%; margin-top: 12%; margin-left: 8%; font-size: 150%;")
    tbody = TBODY()
    tbody.append(TR(TD(STRONG("Problem Name:"),
                    TD(problem_name,
                       _id="problem_name"))))
    tbody.append(TR(TD(STRONG("Problem Link:"),
                    TD(A(I(_class="fa fa-link"), " Link",
                       _href=problem_link)))))
    tbody.append(TR(TD(STRONG("Tags:")),
                   (TD(tags))))
    problem_details.append(tbody)
    table = utilities.render_table(submissions)

    return dict(problem_details=problem_details,
                problem_name=problem_name,
                problem_link=problem_link,
                table=table)

# ----------------------------------------------------------------------------
def tag():
    """
        Tag search page
    """

    table = TABLE(_class="striped centered")
    thead = THEAD(TR(TH("Problem Name"),
                     TH("Problem URL"),
                     TH("Problem Page"),
                     TH("Tags")))
    table.append(thead)

    # If URL does not have vars containing q
    # then remain at the search page and return
    # an empty table
    if request.vars.has_key("q") is False:
        return dict(table=table)

    q = request.vars["q"]
    stable = db.submission
    ptable = db.problem_tags

    query = ptable.tags.like("%" + q + "%")
    join_query = (stable.problem_link == ptable.problem_link)

    all_problems = db(query).select(stable.problem_name,
                                    stable.problem_link,
                                    stable.site,
                                    ptable.tags,
                                    left=ptable.on(join_query),
                                    distinct=True)
    tbody = TBODY()
    for problem in all_problems:
        tr = TR()
        tr.append(TD(A(problem["submission"]["problem_name"],
                       _href=URL("problems",
                                 "index",
                                 vars={"pname": problem["submission"]["problem_name"],
                                       "plink": problem["submission"]["problem_link"]}))))
        tr.append(TD(A(I(_class="fa fa-link"),
                         _href=problem["submission"]["problem_link"])))
        tr.append(TD(problem["submission"]["site"]))
        all_tags = eval(problem["problem_tags"]["tags"])
        td = TD()
        for tag in all_tags:
            td.append(DIV(A(tag,
                            _href=URL("problems",
                                      "tag",
                                      vars={"q": tag}),
                            _style="color: white;"),
                          _class="chip"))
            td.append(" ")
        tr.append(td)
        table.append(tr)
    return dict(table=table)

# ----------------------------------------------------------------------------
def refresh_tags():
    """
        Refresh tags in the database
    """

    ptable = db.problem_tags
    stable = db.submission

    # Problems that are in problem_tags table
    current_problem_list = db(ptable.id > 0).select(ptable.problem_link)
    # Problems that are in submission table
    updated_problem_list = db(stable.id > 0).select(stable.problem_link,
                                                    distinct=True)
    current_problem_list = map(lambda x: x["problem_link"],
                               current_problem_list)
    updated_problem_list = map(lambda x: x["problem_link"],
                               updated_problem_list)

    # Compute difference between the lists
    difference_list = list(set(updated_problem_list) - set(current_problem_list))
    print "Refreshing "

    # Start retrieving tags for the problems
    # that are not in problem_tags table
    for link in difference_list:
        site = urltosite(link)
        try:
            tags_func = getattr(profile, site + "_get_tags")
            all_tags = tags_func(link)
            if all_tags == []:
                all_tags = ["-"]
        except:
            all_tags = ["-"]
        print "."

        # Insert tags in problem_tags table
        # Note: Tags are stored in a stringified list
        #       so that they can be used directly by eval
        ptable.insert(problem_link=link,
                      tags=str(all_tags))

    print "\nNew problems added: " + \
          utilities.RED + \
          " [%d]" % (len(difference_list)) + \
          utilities.RESET_COLOR