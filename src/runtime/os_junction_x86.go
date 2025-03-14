// Copyright 2019 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

//go:build (junction && (386 || amd64)) && !linux
// +build junction,!linux
// +build 386 amd64

package runtime

func osArchInit() {}
