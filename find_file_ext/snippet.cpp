// from Bartek's coding blog
std::vector<std::filesystem::path> paths;

std::filesystem::recursive_directory_iterator dirpos{ root };

std::copy_if( 
    begin( dirpos ), 
    end( dirpos ), 
    std::back_inserter( paths ), 
    [](const std::filesystem::path& p) {
    if (std::filesystem::is_regular_file(p) && p.has_extension())
    {
        auto ext = p.extension();
        return ext == std::string(".txt");
    }
    return false;
});