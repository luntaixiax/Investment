from dataUtils.toolkits.myIO import loadJSON, getFilePath, toJSON


class CONFIG_INVESTMENT:
    INVEST_LIST_PATH = getFilePath("dataUtils/configs/investlist.json")

    @ classmethod
    def getWatchList(cls, product: str) -> list:
        '''
        get watch list from all kinds of investment products
        :param product: {stock, bond, fund}
        :return: the watch list
        '''
        return loadJSON(cls.INVEST_LIST_PATH).get("watch_list", {}).get(product, [])

    @ classmethod
    def addWatchList(cls, product: str, id_list: list) -> None:
        '''
        add new product/investment list to watch list
        :param product: {stock, bond, fund}
        :param id_list: list of new product ids
        :return: None
        '''
        invest_list = loadJSON(cls.INVEST_LIST_PATH)

        if invest_list.get("watch_list") is None:
            invest_list["watch_list"] = {}

        current = invest_list.get("watch_list").get(product, [])
        if len(current) == 0:
            invest_list["watch_list"][product] = id_list
        else:
            for p in id_list:
                if p not in current:
                    current.append(p)

            invest_list["watch_list"][product] = current

        toJSON(invest_list, cls.INVEST_LIST_PATH)


if __name__ == '__main__':
    x = CONFIG_INVESTMENT.getWatchList("bond")
    CONFIG_INVESTMENT.addWatchList("bond", [
            "481001",
            "003095",
            "166002",
            "000572",
            "009860",
            "160222",
            "007020",
            "217011",
            "161716",]
    )