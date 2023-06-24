#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Saving and loading Traits in a JSON file using the json Python module.

This example shows how to save Traits of an object with nested objects, and load
these Traits. In addition, we want to ignore some given nested objects in the
saving/loading process.

Based on a previous example by Pierre Haessig:
https://gist.github.com/pierre-haessig/6543283

Félix Hartmann -- September 2013
'''
from __future__ import division, print_function
import json
from traits.api import HasTraits, Str, Instance, List


def to_json(obj):
    '''return a serialized version of obj
    Return something only if obj's class is in class_dict.'''
    class_dict = {Person: "Person",
                  Household: "Household"}
    if obj.__class__ in class_dict:
        traits_dict = obj.get()
        traits_dict['__class__'] = class_dict[obj.__class__]
        return traits_dict

def from_json(json_obj):
    '''special processes on decoded objects'''
    if "__class__" in json_obj:
        if json_obj["__class__"] == "Person":
            del json_obj["__class__"]
            person = Person()
            person.set(**json_obj)
            return person
        elif json_obj["__class__"] == "Household":
            del json_obj["__class__"]
            return json_obj
        return json_obj


class Person(HasTraits):
    name = Str
    pgp_key_id = Str

    def save_traits(self, fname=None):
        '''save the traits in `fname`
        Saving is done by 'dump' from the json module, with the custum
        serialization function 'to_json'.'''
        with open(fname, 'w') as f:
            json.dump(self, f, indent=4, encoding='utf-8', default=to_json)

    def load_traits(self, fname):
        '''load the traits in `fname`
        Construct a new Person instance from 'fname' with json's 'load' method
        and a custom hook. Then the traits of this instance are set to the
        current instance.'''
        with open(fname, 'r') as f:
            person = json.load(f, encoding='utf-8', object_hook=from_json)
            self.set(**person.get())


class Computer(HasTraits):
    model = Str


class Household(HasTraits):
    address = Str
    residents = List(trait = Person)
    computer = Instance(Computer)   # that trait shall not be saved

    def save_traits(self, fname):
        '''save the traits in `fname`
        Saving is done by 'dump' from the json module, with the custum
        serialization function 'to_json'.'''
        with open(fname, 'w') as f:
            json.dump(self, f, indent=4, encoding='utf-8', default=to_json)

    def load_traits(self, fname):
        '''load the traits in `fname`
        Load a traits dict from 'fname' with json's 'load' method and a custom
        hook. Trait keys whose value is None are removed. Then the remaining
        traits of the dict set to the current instance.'''
        with open(fname, "r") as f:
            traits_dict = json.load(f, object_hook=from_json)
            keys_to_remove = []
            for key, value in traits_dict.iteritems():
                if value is None:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del traits_dict[key]
            self.set(**traits_dict)

    def __str__(self):
        desc = "Address: %s\nComputer model: %s" %(self.address, 
                                                   self.computer.model)
        for i, resident in enumerate(self.residents, 1):
            desc += "\nResident %d:\n\tName: %s\n\tPGP key ID: %s"\
                    %(i, resident.name, resident.pgp_key_id)
        return desc


# Let's define a friendly household
alice = Person(name = "Alice Ziffer", pgp_key_id = "83D3D5AC")
bob = Person(name = "Bob Schlüssel", pgp_key_id = "52D0C87E")
dell = Computer(model = "Dell Latitude")
kryptohaus = Household(
        address = "Enigmastraße 42, Zufallstadt, Schlaraffenland",
        residents = [alice, bob],
        computer = dell
        )
print(kryptohaus)
kryptohaus.save_traits('kryptohaus.json')

print("\nFor some reason, Alice and Bob enter clandestinity, take false "
      "identities, destroy their compromised computer and buy a new cheap "
      "one:")
kryptohaus.address = "nirgendwo"
kryptohaus.residents[0].name = "Ada Geheim"
kryptohaus.residents[0].pgp_key_id = "E29B7C31"
kryptohaus.residents[1].name = "Kim Seeräuber"
kryptohaus.residents[1].pgp_key_id = "60F3A15D"
kryptohaus.computer.model = "Lidl Longitude"
print(kryptohaus)

print("\nAfter a political turnover, Alice and Bob can reintegrate into their "
      "former life (except from the computer):")
kryptohaus.load_traits("kryptohaus.json")
print(kryptohaus.__str__())
