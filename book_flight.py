import argparse
import datetime
import requests
import re




API_URL = "https://api.skypicker.com"


class InputHandler:
    """
        Handling and validating input arguments
    """
    def valid_date_input(self, string):
        try:
            return datetime.datetime.strptime(string, '%Y-%m-%d')
        except ValueError:
            raise argparse.ArgumentTypeError("Not a valid date required format YYYY-MM-DD")

    def valid_iata(self,string):

        if re.match(r'\b[A-Z]{3}\b', string):
            return string
        else:
            raise argparse.ArgumentTypeError("Not a valid form of IATA")

    def date_output(self, date):

        return date.strftime('%d/%m/%Y')

    def getArguments(self):
        parser = argparse.ArgumentParser(description="Book your flight")
        group_required = parser.add_argument_group('required arguments')
        group_required.add_argument('--date', type=self.valid_date_input,
                                    required=True, help="Date of flight you want to book")
        group_required.add_argument('--from', dest='depart', type=self.valid_iata,
                                    required=True, help="IATA code of airport from where flight departures")
        group_required.add_argument('--to', dest='land', type=self.valid_iata,
                                    required=True, help="IATA code of airport where flight arrives")
        group1 = parser.add_mutually_exclusive_group()
        group1.add_argument('--one-way', action='store_true', help="One way flight (default)")
        group1.add_argument('--return', action='store', type=str, dest='round_trip', help="Staying for n nights")
        group2 = parser.add_mutually_exclusive_group()
        group2.add_argument('--cheapest', action='store_true', help="Select cheapest way (default)")
        group2.add_argument('--shortest', action='store_true', help="Select shortest way")
        args=parser.parse_args()

        #Set default arguments
        if not args.shortest:
            args.cheapest = True

        if args.round_trip is None:
            args.one_way = True

        args.date = self.date_output(args.date)

        return args


def flight_payload(args):
    payload = {
        'flyFrom': args.depart,
        'to': args.land,
        'dateFrom':args.date,
        'dateTo': args.date,
    }
    if args.round_trip is not None:
        payload['daysInDestinationFrom'] = args.round_trip
        payload['daysInDestinationTo'] = args.round_trip
        payload['typeFlight'] = 'return'
    elif args.one_way:
        payload['typeFlight'] = 'oneway'
    if args.cheapest:
        payload['sort'] = 'price'
    elif args.shortest:
        payload['sort'] = 'duration'

    return payload


def get_flight(args):
    call = '/flights?v=3'
    url = API_URL + call
    response = requests.get(url,params=flight_payload(args))
    json_data=response.json()

    if json_data['_results'] == 0:
        raise Exception('Flight not found')

    return json_data['data'][0]


def book_flight(args):
    address = 'http://37.139.6.125:8080/booking'
    params = {
        'booking_token': get_flight(args)['booking_token'],
        'currency' : 'EUR',
        'passengers' : [{
            'firstName': 'test',
            'documentID': 'test',
            'birthday': '1900-01-01',
            'email': 'test@test.test',
            'title': 'Mr',
            'lastName': 'test'
        }]
    }

    response = requests.post(address, json=params)
    json_data=response.json()

    if response.status_code == 200:
        if json_data['status'] == 'confirmed':
            return json_data['pnr']
        else: raise Exception('Status not confirmed')
    else:
        raise Exception('Something went wrong, response code:',response.status_code,
                        ', response content:',response.content)



def main():

    input_handler = InputHandler()
    args = input_handler.getArguments()
    print(book_flight(args))


if __name__=='__main__':
    main()
