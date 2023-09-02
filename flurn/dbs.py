import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
import smtplib

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir,'seatInfo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
account_sid = 'ACf28871518b6d85b13347e0e6ad4c5011'
auth_token = 'a142e32767278832adb825a7a83a3dac'
my_email = 'pythonsmtp58@gmail.com'
password = 'xjcxqljmcizxyrbl'
# 8884230038
# Reflect tables from the database
with app.app_context():
    db.Model.metadata.reflect(db.engine)
    table1 = db.Model.metadata.tables['Seats']
    table2 = db.Model.metadata.tables['SeatPricing']
    table3 = db.Model.metadata.tables['Bookings']

    results_from_table1 = db.session.query(table1).all()
    results_from_table2 = db.session.query(table2).all()


class SeatsModel(db.Model):
    __table__ = table1

    def to_dict(self):
        dictionary = {}
        # Loop through each column in the data record
        for column in self.__table__.columns:
            # Create a new dictionary entry;
            # where the key is the name of the column
            # and the value is the value of the column
            if column.name == 'Booking_ID':
                continue
            if column.name == 'status':
                if getattr(self, column.name) == 0:
                    result = False
                else:
                    result = True
                dictionary['is_booked'] = result
            else:
                dictionary[column.name] = getattr(self, column.name)
        return dictionary


class SeatsPricing(db.Model):
    __table__ = table2


class Booking(db.Model):
    __table__ = table3


def get_price(id):
    # result = db.session.execute(db.select(SeatsModel).where(SeatsModel.id == id))
    # result1 = result.scalar()
    seat_class = db.session.execute(db.select(SeatsModel.seat_class).where(SeatsModel.id == id)).scalar()
    booked = db.session.query(SeatsModel).filter(SeatsModel.status == 1, SeatsModel.seat_class == seat_class).count()
    total_class_seats = db.session.query(SeatsModel).filter(SeatsModel.seat_class == seat_class).count()
    if total_class_seats == 0:
        return '$0'
    percentage = booked / total_class_seats
    if percentage < 0.4:
        price = db.session.execute(db.select(SeatsPricing.min_price).where(SeatsPricing.seat_class == seat_class))
        price_val = price.scalar()
        if price_val is not None:
            return price_val
        price = db.session.execute(
                db.select(SeatsPricing.normal_price).where(SeatsPricing.seat_class == seat_class))
    elif 0.4 <= percentage <= 0.6:
        price = db.session.execute(db.select(SeatsPricing.normal_price).where(SeatsPricing.seat_class == seat_class))
        price_val = price.scalar()
        if price_val is not None:
            return price_val
        price = db.session.execute(db.select(SeatsPricing.max_price).where(SeatsPricing.seat_class == seat_class))
    else:
        price = db.session.execute(db.select(SeatsPricing.max_price).where(SeatsPricing.seat_class == seat_class))
        price_val = price.scalar()
        if price_val is not None:
            return price_val
        price = db.session.execute(db.select(SeatsPricing.normal_price).where(SeatsPricing.seat_class == seat_class))
    return price.scalar()


@app.route('/seats', methods=['GET'])
def home():
    result = db.session.execute(db.select(SeatsModel).order_by(SeatsModel.seat_class))
    all_seats = result.scalars().all()
    return jsonify(seats=[seat.to_dict() for seat in all_seats])
# print(results_from_table1)
# print('\n\n\n')
# print(results_from_table2)


@app.route('/seats/<id>', endpoint='seat_id', methods=['GET'])
def seat_id(id):
    result = db.session.execute(db.select(SeatsModel).where(SeatsModel.id == id))
    result1 = result.scalar()
    price = get_price(id)
    return jsonify(Seat_Details={
        "id": result1.id,
        "seat_identifier": result1.seat_identifier,
        "seat_class": result1.seat_class,
        "price": price,
    })


@app.route('/booking', methods=['GET', 'POST'], endpoint='book')
def book():
    id1 = request.args.get('id')
    id_list = id1.split(",")  # request.args.get(id)
    price = 0
    count = 0
    list_seats = []
    for item in id_list:
        is_booked = db.session.execute(db.select(SeatsModel.status).where(SeatsModel.id == item)).scalar()
        if is_booked == 1:
            return jsonify(response={"Failed": f"Seat {item} already Booked"})
        price += float(get_price(item)[1:])

        if count == 0:
            new_booking = Booking(
                Name=request.args.get('name'),
                Ph_no=request.args.get('phone'),
                email=request.args.get('email')
            )
            db.session.add(new_booking)
            count += 1
        seat = db.session.execute(db.select(SeatsModel.id).where(SeatsModel.id == item))
        if seat.scalar() is None:
            return jsonify(response={"Failed": f"Seat {item} does not exist"})
        seat = db.get_or_404(SeatsModel, item)
        seat.status = 1
        list_seats.append(item)
        last_row = db.session.query(Booking).order_by(Booking.BookingID.desc()).first()
        seat.Booking_ID = last_row.BookingID
    db.session.commit()
    booking_id = db.session.query(Booking).order_by(Booking.BookingID.desc()).first().BookingID
    twillio_client = Client(account_sid, auth_token,)
    message = twillio_client.messages.create(body=f'Booking Confirmed \nBooking ID: {booking_id}\nSeats: {id1}',
                                     from_='+16562162318',
                                     to='+918884230038')
    receiver_email = request.args.get('email')
    with smtplib.SMTP('smtp.gmail.com', port=587) as connection:
        connection.starttls()
        connection.login(user=my_email, password=password)
        connection.sendmail(from_addr=my_email,
                            to_addrs=receiver_email,
                            msg=f'Subject: Booking confirmed\n\nBooking Confirmed\nBooking ID:{booking_id}\nSeats:{id1}')
    return jsonify(response={"Success": "Booking successful",
                             "Booking_ID": booking_id,
                             "Total_amount": f"${price:.2f}",})


@app.route('/bookings', methods=['GET'], endpoint='retrieve_bookings')
def retrieve_bookings():
    user_identifier = request.args.get('userIdentifier')
    if not user_identifier:
        return jsonify(response={'error': 'User Identifier not provided'})
    if user_identifier.isnumeric():
        booking_id = db.session.execute(db.select(Booking.BookingID).where(Booking.Ph_no == user_identifier))
        if booking_id.scalar() is None:
            return jsonify({'Error': 'User has no bookings'})
        else:
            b_id = db.session.execute(db.select(Booking.BookingID).where(Booking.Ph_no == user_identifier)).scalar()
            result = db.session.execute(db.select(SeatsModel).where(SeatsModel.Booking_ID == b_id))
            all_seats = result.scalars()
            return jsonify(seats=[seat.to_dict() for seat in all_seats])
    else:
        return jsonify(response={'Error': 'Invalid User Identifier'})


if __name__ == "__main__":
    app.run(debug=True)
