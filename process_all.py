import os
from components import pipeline
from components.munisource import nj_millburn


import pprint

if __name__ == "__main__":
    for doctype in nj_millburn.DOCTYPES:
        for year in nj_millburn.YEARS_TO_PROCESS:
            sources = nj_millburn.get_sources(doctype, year)
            for source in sources:
                pprint.pprint(source)
                result = pipeline.reshape_to_pipeline_result(pipeline.pipeline(source))
                ids = pipeline.persist(source, result)
                pipeline.print_pipeline_results(result)
                print(ids)
