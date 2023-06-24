// https://twitter.com/neelabalan/status/1291346234809098240?s=20
//
#include <bitset>
#include <iostream>
#include <string_view>
#include <vector>
#include <array>

std::string encode(std::string data)
{
    	const std::string_view base64chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
	unsigned int dlength = data.length();
	unsigned short padcount = dlength % 3;
    	std::string str {""};
    	std::string encodedstring = "";

    	for ( auto i = 0; i < dlength; i += 3)
	{
		std::array<std::bitset<6>, 4> buffer;
		buffer[0] = data[i] >> 2;
		buffer[1] = std::bitset<6>(data[i] << 4) ^ std::bitset<6>(data[i+1] >> 4);
		buffer[2] = std::bitset<6>(data[i+1] << 2) ^ std::bitset<6>(data[i+2] >> 6);
		buffer[3] = std::bitset<6>(data[i+2]);

		for (auto set : buffer) {
			str += base64chars[set.to_ulong()];
		}
    	}    
    	if(padcount)
	{
        	encodedstring = str.replace(
			str.length() - padcount -1, 
			str.length(), 
			std::string("===").substr(0, padcount+1)
        	);
    	}
    	else { encodedstring = str; }
	return encodedstring;
}

int main() 
{
    	std::string data {""};
	std::cin>>data;
	std::cout<<encode(data);
	return 0;
}
