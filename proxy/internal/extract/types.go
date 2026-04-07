package extract

type Value struct {
	Path  string `json:"path"`
	Value string `json:"value"`
}

type CurrentNode struct {
	Node any
	Path string
}

type CompiledPath struct {
	RawPath  string
	Segments []Segment
}

const (
	FieldSegment SegmentKind = iota
	WildcardSegment
	IndexSegment
)

type SegmentKind int
type Segment struct {
	Kind  SegmentKind
	Field string
	Index int
}
