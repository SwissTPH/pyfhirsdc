//source https://cql.hl7.org/grammar.html

grammar fhirpath;

// Grammar rules
// [FHIRPath](http://hl7.org/fhirpath/N1) Normative Release

//prog: line (line)*;
//line: ID ( '(' expr ')') ':' expr '\r'? '\n';

expression
        : pysdcexpression 
        | term                                     
        | expression '.' invocation                                 
        | expression '[' expression ']'                             
        | ('+' | '-') expression                                    
        | expression ('*' | '/' | 'div' | 'mod') expression         
        | expression ('+' | '-' | '&') expression                   
        | expression ('is' | 'as') typeSpecifier                    
        | expression '|' expression                                 
        | expression ('<=' | '<' | '>' | '>=') expression           
        | expression ('=' | '~' | '!=' | '!~') expression           
        | expression ('in' | 'contains') expression                 
        | expression 'and' expression                               
        | expression ('or' | 'xor') expression                      
        | expression 'implies' expression                           
        //| (IDENTIFIER)? '=>' expression                             
        ;
pysdcexpression 
        :  ('o'|'v'|'c')?QUOTEDIDENTIFIER ('<<'|'!<<'|'='|'!=') ('o'|'v')?QUOTEDIDENTIFIER      #pse1
        | ('o'|'v'|'c')?QUOTEDIDENTIFIER (('='|'!='|'<'|'>'|'<='|'>=') literal)?                #pse2
        ;
        
term
        : invocation                                            
        | literal                                               
        | externalConstant                                      
        | '(' expression ')'                                    
        ;

literal
        : '{' '}'                                               
        | ('true' | 'false')                                    
        | STRING                                                
        | NUMBER                                                
        | DATE                                                  
        | DATETIME                                              
        | TIME                                                  
        | quantity                                              
        ;

externalConstant
        : '%' ( identifier | STRING )
        ;

invocation                          // Terms that can be used after the function/member invocation '.'
        : identifier                                            
        | function                                              
        | '$this'                                               
        | '$index'                                              
        | '$total'                                              
        ;

function
        : identifier '(' paramList? ')'
        ;

paramList
        : expression (',' expression)*
        ;

quantity
        : NUMBER unit?
        ;

unit
        : dateTimePrecision
        | pluralDateTimePrecision
        | STRING // UCUM syntax for units of measure
        ;

dateTimePrecision
        : 'year' | 'month' | 'week' | 'day' | 'hour' | 'minute' | 'second' | 'millisecond'
        ;

pluralDateTimePrecision
        : 'years' | 'months' | 'weeks' | 'days' | 'hours' | 'minutes' | 'seconds' | 'milliseconds'
        ;

typeSpecifier
        : qualifiedIdentifier
        ;

qualifiedIdentifier
        : identifier ('.' identifier)*
        ;

identifier
        : IDENTIFIER                            
        | DELIMITEDIDENTIFIER                   #delimitedidentifier
        | 'as'                                  
        | 'contains'                            
        | 'in'                                          
        | 'is'                                          
        ;


/****************************************************************
    Lexical rules
*****************************************************************/

/*
NOTE: The goal of these rules in the grammar is to provide a date
token to the parser. As such it is not attempting to validate that
the date is a correct date, that task is for the parser or interpreter.
*/

DATE
        : '@' DATEFORMAT
        ;

DATETIME
        : '@' DATEFORMAT 'T' (TIMEFORMAT TIMEZONEOFFSETFORMAT?)?
        ;

TIME
        : '@' 'T' TIMEFORMAT
        ;

fragment DATEFORMAT
        : [0-9][0-9][0-9][0-9] ('-'[0-9][0-9] ('-'[0-9][0-9])?)?
        ;

fragment TIMEFORMAT
        : [0-9][0-9] (':'[0-9][0-9] (':'[0-9][0-9] ('.'[0-9]+)?)?)?
        ;

fragment TIMEZONEOFFSETFORMAT
        : ('Z' | ('+' | '-') [0-9][0-9]':'[0-9][0-9])
        ;

IDENTIFIER
        : ([A-Za-z] | '_')([A-Za-z0-9] | '_')*            // Added _ to support CQL (FHIR could constrain it out)
        ;

DELIMITEDIDENTIFIER
        : '`' (ESC | .)*? '`'
        ;
QUOTEDIDENTIFIER
    : '"' (ESC | .)*? '"'
    ;

STRING
        : '\'' (ESC | .)*? '\''
        ;

// Also allows leading zeroes now (just like CQL and XSD)
NUMBER
        : [0-9]+('.' [0-9]+)?
        ;

// Pipe whitespace to the HIDDEN channel to support retrieving source text through the parser.
WS
        : [ \r\n\t]+ -> channel(HIDDEN)
        ;

COMMENT
        : '/*' .*? '*/' -> channel(HIDDEN)
        ;

LINE_COMMENT
        : '//' ~[\r\n]* -> channel(HIDDEN)
        ;

fragment ESC
        : '\\' ([`'\\/fnrt] | UNICODE)    // allow \`, \', \\, \/, \f, etc. and \uXXX
        ;

fragment UNICODE
        : 'u' HEX HEX HEX HEX
        ;

fragment HEX
        : [0-9a-fA-F]
        ;