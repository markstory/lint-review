package main

import (
	"fmt"
	"flag"
	"github.com/kr/pretty"
)

type Person struct {
	name string
}

func main() {
	flag.Parse()
	person := Person{flag.Arg(0)}

	fmt.Printf("Hello %s", pretty.Formatter(person))
}
