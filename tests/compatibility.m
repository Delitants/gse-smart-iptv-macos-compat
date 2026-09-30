#import <Cocoa/Cocoa.h>
#import <dlfcn.h>
#import <objc/runtime.h>
static int failures;
extern void testEPGPop(id,SEL);
extern char testEPGReturnAddress;
#define CHECK(c,m) do { if (!(c)) { fprintf(stderr,"FAIL: %s\n",m); failures++; } else puts("PASS: " m); } while(0)
@interface ActionOwner:NSObject <NSTableViewDelegate>
-(void)doubleClickedRow:(id)sender;
@end
@implementation ActionOwner
-(void)doubleClickedRow:(id)sender {}
@end
static int receiptRequests;
@interface DistributionDelegate:NSObject
-(void)strategicPlace1;
@end
@implementation DistributionDelegate
-(void)strategicPlace1 { receiptRequests++; }
@end
int main(int argc,char **argv) { @autoreleasepool {
 void *lib=argc>1?dlopen(argv[1],RTLD_NOW):NULL;
 void (*install)(uintptr_t)=lib?dlsym(lib,"GSEInstallCompatibility"):NULL;
 void (*removeAt)(NSMutableArray*,NSUInteger,uintptr_t)=lib?dlsym(lib,"GSECheckedRemoval"):NULL;
 uintptr_t known=(uintptr_t)&testEPGReturnAddress;
 if(install)install(known);
 ActionOwner *owner=[ActionOwner new]; NSTableView *t=[NSTableView new];
 t.delegate=owner; t.doubleAction=@selector(doubleClickedRow:);
 CHECK(t.target==owner,"double action gets its controller target");
 NSTableView *late=[NSTableView new]; late.doubleAction=@selector(doubleClickedRow:); late.delegate=owner;
 CHECK(late.target==owner,"delegate assigned later gets navigation target");
 NSTableView *explicit=[NSTableView new]; NSObject *other=[NSObject new]; explicit.target=other; explicit.delegate=owner; explicit.doubleAction=@selector(doubleClickedRow:);
 CHECK(explicit.target==other,"explicit targets stay intact");
 NSTableView *unrelated=[NSTableView new]; unrelated.delegate=owner; unrelated.doubleAction=@selector(description);
 CHECK(unrelated.target==nil,"unrelated actions stay intact");
 NSMutableArray *empty=[NSMutableArray array]; BOOL threw=NO;
 @try {if(removeAt)removeAt(empty,0,known);else [empty removeObjectAtIndex:0];} @catch(NSException *e){threw=YES;}
 CHECK(!threw && empty.count==0,"late EPG completion with empty queue is harmless");
 NSMutableArray *queue=[NSMutableArray arrayWithArray:@[@"first",@"second"]];
 if(removeAt)removeAt(queue,0,known);else [queue removeObjectAtIndex:0];
 CHECK([queue isEqualToArray:@[@"second"]],"normal EPG completion removes only first item");
 threw=NO; @try {if(removeAt)removeAt(empty,0,0x5678);else [empty removeObjectAtIndex:0];} @catch(NSException *e){threw=YES;}
 CHECK(threw,"unrelated empty array misuse still raises an exception");
 threw=NO; @try {if(removeAt)removeAt(queue,9,known);else [queue removeObjectAtIndex:9];} @catch(NSException *e){threw=YES;}
 CHECK(threw,"other invalid indices still raise an exception");
 threw=NO; @try {testEPGPop(empty,@selector(removeObjectAtIndex:));} @catch(NSException *e){threw=YES;}
 CHECK(!threw,"real Objective-C dispatch guards the exact native return address");
 BOOL (*direct)(Class,uintptr_t)=lib?dlsym(lib,"GSEInstallDirectDistribution"):NULL;
 Class delegate=[DistributionDelegate class];
 uintptr_t original=(uintptr_t)class_getMethodImplementation(delegate,@selector(strategicPlace1));
 CHECK(direct!=NULL,"direct distribution installer is available");
 if(direct) {
  CHECK(!direct([NSObject class],original),"missing receipt method is rejected");
  CHECK(!direct(delegate,original+1),"unexpected receipt implementation is rejected");
  [[DistributionDelegate new] strategicPlace1];
  CHECK(receiptRequests==1,"rejected patch leaves original method intact");
  CHECK(direct(delegate,original),"known delayed receipt callback is replaced");
  [[DistributionDelegate new] strategicPlace1];
  CHECK(receiptRequests==1,"direct distribution queues no receipt check");
 }
 return failures?1:0;
}}
