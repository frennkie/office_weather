# -*- coding: utf-8 -*-


def get_values():
    """generator"""
    while True:
        entered_data = raw_input("Please enter something: ")
        yield "prefix_", entered_data


def create_dataset(_config, tmp=None, co2=None):
    """create and return a json dataset ready to sent to API as POST"""

    sensor = _config["sensor"]
    office = _config["office"]

    json_body = [
        {
            "measurement": "tmp",
            "tags": {
                "sensor": sensor,
                "office": office
            },
            "fields": {
                "value": tmp
            }
        },
        {
            "measurement": "co2",
            "tags": {
                "sensor": sensor,
                "office": office
            },
            "fields": {
                "value": co2
            }
        }
    ]

    return json_body


def create_dataset2(tags, **kwargs):
    """create and return a json dataset ready to sent to API as POST

    Args:
        tags (dict): A dict of tags that will be associated with the data points
        **kwargs: keyword arguments containing the values will be put into the db

    Returns:
        dataset in json format that should then be sent as the POST body
    """

    json_body = list()

    for key in kwargs:
        dct = {
            "measurement": key,
            "tags": tags,
            "fields": {
                "value": kwargs[key]
            }
        }
        json_body.append(dct)

    return json_body


class Shape(object):
    def __init__(self, shapename, **kwds):
        self.shapename = shapename
        super(Shape, self).__init__(**kwds)

class ColoredShape(Shape):
    def __init__(self, color, **kwds):
        self.color = color
        super(ColoredShape, self).__init__(**kwds)


def main():
    """main"""

    my_shape = Shape(shapename="my_shape1")
    print(my_shape.shapename)

    my_c_shape = ColoredShape(shapename="my_shape1", color="red")
    print(my_c_shape.shapename)
    print(my_c_shape.color)

    """
    print("Start")

    for prefix, enter in get_values():
        print("for_loop")
        print(prefix + " _-_ " + enter)

    print("End")
    """

    """
    config = {"sensor": "my_sensor1", "office": "main_floor"}

    cur_tmp = 23.445
    cur_co2 = 758

    one = create_dataset(config, tmp=cur_tmp, co2=cur_co2)
    two = create_dataset2(config, tmp=cur_tmp, co2=cur_co2)

    print(one)
    print(two)
    print("same?")
    print(one == two)
    """


if __name__ == "__main__":
    main()
