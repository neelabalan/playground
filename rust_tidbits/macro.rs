macro_rules! print_lines {
    ( $( $line:expr), * ) => {
        $(
            println!("{}", $line);
        )*
    };
}

fn main() {
    print_lines!(
        "Hello, world!",
        "This is a macro!",
    );
}