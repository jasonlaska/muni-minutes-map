from components.munisource.nj_millburn import NJMillburnCrawler, NJMillburnDownloader


if __name__ == "__main__":
    ### --- MILBURN --- ###
    crawler = NJMillburnCrawler()
    minutes = crawler.crawl()
    timestamp = crawler.save()
    print("Latest @ ", timestamp)
    NJMillburnDownloader(timestamp).download()
