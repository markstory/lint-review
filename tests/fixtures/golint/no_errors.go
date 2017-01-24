package main

import (
	"fmt"
	"flag"
)

func main() {
	flag.Parse()

	fmt.Printf("Hello %s", flag.Arg(0))
}
