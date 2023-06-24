# danionescu0/docker-flask-mongodb-example
# ---for testing random---
http http://localhost:800/random-list
http http://localhost:800/random upper==100 lower==10

http -f PUT http://localhost:800/random lower=10 upper=50

#---user crud test---
# adding users
http -f PUT http://localhost:81/users/1 email=john@doe.com name=John
http -f PUT http://localhost:81/users/2 email=steve@rogers.com name=Steve
http -f PUT http://localhost:81/users/3 email=change@user.com name=Change

# change email of user 3
http -f POST http://localhost:81/users/3 email=newuser@user.com

# check the change
http http://localhost:81/users/3

# delete user 3
http DELETE http://localhost:81/users/3

# check if delete works
http http://localhost:81/users


#---fulltext search---
http -f PUT http://localhost:82/fulltext expression="Who has many apples"
http -f PUT http://localhost:82/fulltext expression="The apple tree grew in the park"
http -f PUT http://localhost:82/fulltext expression="Some apples are green and some are yellow"
http -f PUT http://localhost:82/fulltext expression="How many trees are there in this forest"

http http://localhost:82/search/apples

#---geo location search---
http -f POST http://localhost:83/location name=Bucharest lat="26.1496616" lng="44.4205455"

http http://localhost:83/location/26.1/44.4

http http://localhost:83/location/26.1/44.4 max_distance==50000

#---Bayesian average---
http -f POST http://localhost:84/item/1 name=Hamlet
http -f POST http://localhost:84/item/2 name=Cicero
http -f POST http://localhost:84/item/3 name=Alfred

http -f PUT http://localhost:84/item/vote/1 mark=9 userid=1
http -f PUT http://localhost:84/item/vote/2 mark=9 userid=4
http -f PUT http://localhost:84/item/vote/3 mark=7 userid=6

http DELETE http://localhost:84/item/3

http http://localhost:84/item/1
http http://localhost:84/items

#---photo process---
http -f PUT http://localhost:85/photo/1 file@image1.jpeg
http -f PUT http://localhost:85/photo/2 file@image2.jpeg

http http://localhost:85/photo/1 resize==100 > image1resize.jpeg

http -f PUT http://localhost:85/photo/similar file@image1resize.jpeg

http DELETE http://localhost:85/photo/2


#---book collection---
http -f --json PUT "http://localhost:86/book/978-1607965503" \
    name="Lincoln the unknown" \
    isbn="978-1607965503" \
    author="Dale Carnegie" \
    publisher="snowball publishing" \
    nr_available:=5

http -f --json PUT "http://localhost:86/book/9780262529624" \
    name="Intro to Computation and Programming using Python" \
    isbn="9780262529624" \
    author="John Guttag" \
    publisher="MIT Press" \
    nr_available:=3


http -f http://localhost:86/book/9780262529624

http DELETE http://localhost:86/book/9780262529624

http http://localhost:86/book limit==5 offset==0

# borrow book
http -f --json PUT http://localhost:86/borrow/978-1607965503 \
    id=1 \
    userid=1 \
    isbn="978-1607965503" \
    borrow_date="2019-12-12T09:32:51.715Z" \
    return_date="2020-02-12T09:32:51.715Z" \
    max_return_date="2020-03-12T09:32:51.715Z"

# list a borrowed book
http http://localhost:86/borrow/978-1607965503 

http -f --json PUT http://localhost:86/borrow/return/978-1607965503 id="978-1607965503"  return_date="2020-02-12T09:32:51.715Z"

http http://localhost:86/borrow limit==5 offset==0


#---fastapi user CRUD---

http -f --json PUT http://localhost:88/users/1 userid=1 email=john@doe.com name=John
http -f --json PUT http://localhost:88/users/3 userid=3 email=change@user.com name=Change

http http://localhost:88/users/2
http -f --json POST http://localhost:88/users/3 userid=3 email=user@user.com name=Change

http DELETE http://localhost:88/users/1
http http://localhost:88/users

echo -n humidity value=66 | http POST http://localhost:8086/write?db=influx


# mqtt service
# new terminal
mosquitto_pub -h localhost -u some_user -P some_pass -p 1883 -d -t sensors -m "{\"sensor_id\": \"temperature\", \"sensor_value\": 15.2}"

# new terminal for sub
mosquitto_sub -h localhost -u some_user -P some_pass -p 1883 -d -t sensors
