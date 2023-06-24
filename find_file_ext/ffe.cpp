/*
> how to compile?
g++ -std=c++17 -pthread directory-listing.cpp -o ffe

usage 
// to find the total number of markdown files in that directory and subdirectories
    ffe .md 
// to show the path
    ffe .cpp --showpath

*/
#include <iostream>
#include <string>
#include <filesystem>
#include <future>
#include <vector>
#include <algorithm>

namespace fs = std::filesystem;

std::pair< std::string, bool > parse_args( int, char** );
unsigned int find_files_count( std::string, bool );
unsigned int find_files_recursive( fs::path, std::string, bool );
bool is_file_with_extension( fs::path, std::string, bool );

int main(int argc, char** argv)  
{
    bool showpath = false;
    std::string extension {};
    std::tie( extension, showpath ) = parse_args( argc, argv );
    if( extension.length() > 0 ){
        std::cout << find_files_count( extension, showpath ) << " files found with extension " << extension;
    }
}

bool is_file_with_extension( fs::path file_path, std::string extension, bool showpath )
{
    if( file_path.has_extension() && file_path.extension() == extension ) 
    {
        if ( showpath ){
            std::cout << file_path.string() << std::endl;
        }
        return true;
    }
    else
    {
        return false;
    }
}

unsigned int find_files_recursive( fs::path dirpath, std::string extension, bool showpath )
{
    fs::recursive_directory_iterator dir_iterator { dirpath };
    unsigned int file_count = std::count_if(
        begin( dir_iterator ),
        end( dir_iterator ),
        [ extension, showpath ]( const std::filesystem::path &p ) {
            return is_file_with_extension( p, extension, showpath );
        }
    );
    return file_count;
}

unsigned int find_files_count( std::string extension, bool showpath ) 
{
    unsigned int file_count = 0;
    std::vector< std::future < unsigned int > > futures;
    for ( const auto &entry : fs::directory_iterator( "." ) )
    {
        if( fs::is_directory( entry ) )
        {
           futures.emplace_back( 
               std::async( 
                   std::launch::async, 
                   find_files_recursive, 
                   entry, 
                   extension,
                   showpath 
                ) 
            ); 
        } 
        else
        {
            if ( is_file_with_extension( entry, extension, showpath ) ) 
            {
                file_count++;
            }
        }
    }
    for( auto &future : futures ) 
    {
        unsigned int count = future.get();
        file_count = file_count + count;
    }
    return file_count;
}

std::pair< std::string, bool > parse_args( int argc, char** argv ) {
    bool showpath = false;
    std::string extension {};

    if ( argc > 1 ) {
        extension = argv[1];
    }
    if ( argc > 2 ) {
        showpath = std::string( "--showpath" ) == std::string( argv[2] );
    }
    return std::make_pair( extension, showpath );
}